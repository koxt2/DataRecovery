# Copyright 2025 Richard Potts
# SPDX-License-Identifier: GPL-2.0-or-later

import logging
import os
import threading
import traceback

from gi.repository import Adw, GLib

from .block_devices import check_sufficient_space, get_image_size
from .config import RECOVERED_FILES_DIR, RECOVERY_DATA_FOLDER
from .duplicates import DuplicateRemover
from .file_operations import FileOperations
from .imager import DeviceImager
from .map_health import MapHealth
from .recover import DeviceRecovery
from .utils import format_bytes


class RecoveryWorkflow:
    def __init__(self, window, working_dir, recovery_dialog):
        self.window = window
        self.working_dir = working_dir
        self.recovery_dialog = recovery_dialog
        self.logger = logging.getLogger("datarecovery")

        self.device_imager = DeviceImager(recovery_dialog)
        self.file_operations = FileOperations(recovery_dialog)
        self.photorec_recovery = DeviceRecovery(recovery_dialog)
        self.duplicate_remover = DuplicateRemover(recovery_dialog, working_dir)

    def start_recovery(self, device_path, user_settings):
        self.logger.info("Starting recovery using...")
        self.logger.info(f"working_dir: {self.working_dir}")
        self.logger.info(f"device_path: {device_path}")
        self.logger.info(f"destination_path: {getattr(self.window, 'destination_path', None)}")
        self.logger.info(f"user_settings: {user_settings}")

        is_image_file = os.path.isfile(device_path) if device_path else False

        self.recovery_dialog.show()

        steps = []

        # Only add imaging step for physical devices
        if not is_image_file:
            steps.append(("imaging", "Create disk image"))

        steps.append(("recovery", "Recover files"))

        # Add optional steps based on settings
        if user_settings.get("remove_duplicates", False):
            steps.append(("duplicates", "Remove duplicate files"))

        destination_path = getattr(self.window, "destination_path", None)

        steps.append(("organize", "Organize files by type"))

        if destination_path and user_settings.get("save_image", False) and not is_image_file:
            steps.append(("save_images", "Save disk images"))

        if destination_path:
            steps.append(("save_logs", "Save logs"))

        self.recovery_dialog.setup_steps(steps)

        self.recovery_dialog.cancel_callback = self._create_cancel_callback()

        thread = threading.Thread(
            target=self._run_recovery_thread,
            args=(device_path, user_settings, is_image_file),
            daemon=True,
        )
        thread.start()

    def _offer_health_view(self, mapfile_path, saved):
        body = (
            "ddrescue recorded which parts of the drive could be read. "
            "Do you want to view a graphical map of the scan to see how healthy the drive is."
        )
        if saved:
            body += (
                f"\n\nThe map file is saved in the “{RECOVERY_DATA_FOLDER}” folder, "
                "so you can analyse it again later."
            )
        else:
            body += (
                "\n\nThe map file is not kept unless you choose to save the disk image, "
                "so this is your only chance to view it."
            )
        dialog = Adw.AlertDialog.new("View Drive Health?", body)
        dialog.add_response("no", "No")
        dialog.add_response("yes", "View")
        dialog.set_response_appearance("yes", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("yes")
        dialog.set_close_response("no")

        def on_response(_dialog, response):
            if response == "yes":
                MapHealth(parent=self.window)(mapfile_path)

        dialog.connect("response", on_response)
        dialog.present(self.window)
        return False

    def _create_cancel_callback(self):
        def cancel_recovery():
            self.logger.warning("Cancelling recovery operations...")
            self.device_imager.cancel()
            self.photorec_recovery.cancel()
            self.duplicate_remover.cancel()
            GLib.idle_add(self.recovery_dialog.update_status, "Cancelling recovery... cleaning up")

            def cleanup_thread():
                self.file_operations.cleanup_working_directory(self.working_dir)
                GLib.idle_add(
                    self.recovery_dialog.update_status,
                    "Recovery cancelled - cleanup complete",
                )

            cleanup = threading.Thread(target=cleanup_thread, daemon=True)
            cleanup.start()

        return cancel_recovery

    def _run_recovery_thread(self, device_path, user_settings, is_image_file):
        try:
            destination_path = getattr(self.window, "destination_path", None)
            keep_corrupted = user_settings.get("keep_corrupted", False)
            remove_duplicates = user_settings.get("remove_duplicates", False)
            save_image = user_settings.get("save_image", False)

            # Check there is enough space on destination for recovered files (and images if applicable)
            if destination_path:
                if is_image_file:
                    source_size = get_image_size(device_path)
                    is_sufficient, device_size, dest_available, dest_required = (
                        check_sufficient_space(
                            device_path, destination_path, source_size=source_size
                        )
                    )
                else:
                    is_sufficient, device_size, dest_available, dest_required = (
                        check_sufficient_space(device_path, destination_path)
                    )
                if not is_sufficient:
                    content = "image and recovered files" if save_image else "recovered files"
                    self.logger.error(
                        f"Insufficient space at destination for {content}: need {dest_required:,} bytes but only {dest_available:,} bytes available at {destination_path}"
                    )
                    GLib.idle_add(
                        self.recovery_dialog.update_status,
                        f"Insufficient space at destination: need {format_bytes(dest_required)} but only {format_bytes(dest_available)} available",
                    )
                    return

            # Step 1: Create disk images (only for physical devices, not image files)
            if not is_image_file:
                GLib.idle_add(self.recovery_dialog.update_step_status, "imaging", "active")
                imaging_success = self.device_imager.setup_imager(device_path, self.working_dir)

                if not imaging_success:
                    if self.device_imager.cancelled:
                        self.logger.info("Disk imaging cancelled by user")
                        GLib.idle_add(self.recovery_dialog.update_step_status, "imaging", "error")
                        self.file_operations.cleanup_working_directory(self.working_dir)
                        return
                    self.logger.error("Disk imaging failed")
                    GLib.idle_add(self.recovery_dialog.update_step_status, "imaging", "error")
                    GLib.idle_add(
                        self.recovery_dialog.update_status,
                        "Recovery failed: Disk imaging unsuccessful",
                    )
                    self.file_operations.cleanup_working_directory(self.working_dir)
                    return

                GLib.idle_add(self.recovery_dialog.update_step_status, "imaging", "complete")
            else:
                self.logger.info(f"Using existing image file: {device_path}")

            # Step 2: Run PhotoRec to recover files from images
            GLib.idle_add(self.recovery_dialog.update_step_status, "recovery", "active")
            GLib.idle_add(
                self.recovery_dialog.update_progress, 0
            )  # Reset progress bar for PhotoRec
            recovery_dir = os.path.join(self.working_dir, RECOVERED_FILES_DIR)

            # For image files, pass the file path directly to PhotoRec
            # For devices, use the working_dir where images were created
            recovery_source = device_path if is_image_file else self.working_dir
            recovery_success = self.photorec_recovery.setup_recovery(
                recovery_source, recovery_dir, keep_corrupted
            )

            if not recovery_success:
                if self.photorec_recovery.cancelled:
                    self.logger.info("PhotoRec recovery cancelled by user")
                    GLib.idle_add(self.recovery_dialog.update_step_status, "recovery", "error")
                    return
                self.logger.error("PhotoRec recovery failed")
                GLib.idle_add(self.recovery_dialog.update_step_status, "recovery", "error")
                GLib.idle_add(
                    self.recovery_dialog.update_status,
                    "Recovery failed: PhotoRec unsuccessful",
                )
                return

            GLib.idle_add(self.recovery_dialog.update_step_status, "recovery", "complete")

            # Step 3: Remove duplicates if requested
            if remove_duplicates:
                GLib.idle_add(self.recovery_dialog.update_step_status, "duplicates", "active")
                GLib.idle_add(self.recovery_dialog.update_status, "Removing duplicate files")
                self.duplicate_remover.remove_duplicates(recovery_dir)
                GLib.idle_add(self.recovery_dialog.update_step_status, "duplicates", "complete")

            # Step 4: Organize recovered files by type (only selected extensions)
            GLib.idle_add(self.recovery_dialog.update_step_status, "organize", "active")
            GLib.idle_add(self.recovery_dialog.update_progress, 0)
            GLib.idle_add(self.recovery_dialog.update_status, "Organizing files by type")
            selected_extensions = user_settings.get("selected_extensions", [])
            self.file_operations.organize_recovered_files(
                recovery_dir, destination_path, selected_extensions
            )
            GLib.idle_add(self.recovery_dialog.update_step_status, "organize", "complete")

            # Step 5: Move images if requested
            mapfile_path = self.device_imager.mapfile_path if not is_image_file else None
            saved = False
            if destination_path and user_settings.get("save_image", False):
                GLib.idle_add(self.recovery_dialog.update_step_status, "save_images", "active")
                GLib.idle_add(self.recovery_dialog.update_status, "Saving disk images")
                self.file_operations.move_images_to_destination(self.working_dir, destination_path)
                if mapfile_path:
                    saved = True
                    mapfile_path = os.path.join(
                        destination_path, RECOVERY_DATA_FOLDER, os.path.basename(mapfile_path)
                    )
                GLib.idle_add(self.recovery_dialog.update_step_status, "save_images", "complete")

            # Step 6: Move logs (always done when destination is set)
            if destination_path:
                GLib.idle_add(self.recovery_dialog.update_step_status, "save_logs", "active")
                GLib.idle_add(self.recovery_dialog.update_status, "Saving logs")
                self.file_operations.move_logs_to_destination(self.working_dir, destination_path)
                GLib.idle_add(self.recovery_dialog.update_step_status, "save_logs", "complete")

            self.logger.info("Recovery completed successfully")
            GLib.idle_add(self.recovery_dialog.update_status, "Recovery complete")
            GLib.idle_add(self.recovery_dialog.mark_complete)

            if mapfile_path and os.path.isfile(mapfile_path):
                GLib.idle_add(self._offer_health_view, mapfile_path, saved)

        except Exception as e:
            self.logger.error(f"Recovery failed with exception: {e}")
            self.logger.error(traceback.format_exc())
            GLib.idle_add(self.recovery_dialog.update_status, f"Recovery failed: {str(e)}")

            error_message = str(e)

            def show_error_dialog():
                error_dialog = Adw.AlertDialog.new("Recovery Failed", None)
                error_dialog.set_body(
                    f"An error occurred during recovery:\n\n{error_message}\n\nCheck logs for details."
                )
                error_dialog.add_response("ok", "OK")
                error_dialog.set_default_response("ok")
                error_dialog.present(self.window)

            GLib.idle_add(show_error_dialog)
