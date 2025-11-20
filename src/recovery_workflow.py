# recovery_workflow.py
#
# Copyright 2025 koxt2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os
import logging
import threading
import traceback
from gi.repository import GLib, Adw
from .imager import DeviceImager
from .file_operations import FileOperations
from .recover import DeviceRecovery
from .duplicates import DuplicateRemover
from .config import RECOVERED_FILES_DIR
from .block_devices import check_sufficient_space


class RecoveryWorkflow:
    def __init__(self, window, working_dir, recovery_dialog):
        self.window = window
        self.working_dir = working_dir
        self.recovery_dialog = recovery_dialog
        self.logger = logging.getLogger('datarecovery')
        
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
            steps.append(('imaging', 'Create disk images'))
        
        steps.append(('recovery', 'Recover files'))
        
        # Add optional steps based on settings
        if user_settings.get("remove_duplicates", False):
            steps.append(('duplicates', 'Remove duplicate files'))
        
        destination_path = getattr(self.window, 'destination_path', None)
        
        steps.append(('organize', 'Organize files by type'))
        
        if destination_path and user_settings.get("save_image", False) and not is_image_file:
            steps.append(('save_images', 'Save disk images'))
        
        if destination_path and user_settings.get("save_logs", False):
            steps.append(('save_logs', 'Save logs'))
        
        self.recovery_dialog.setup_steps(steps)
        
        self.recovery_dialog.cancel_callback = self._create_cancel_callback()
        
        thread = threading.Thread(
            target=self._run_recovery_thread,
            args=(device_path, user_settings, is_image_file),
            daemon=True
        )
        thread.start()
    
    def _create_cancel_callback(self):
        def cancel_recovery():
            self.logger.warning("Cancelling recovery operations...")
            self.device_imager.cancel()
            self.photorec_recovery.cancel()
            self.duplicate_remover.cancel()
            GLib.idle_add(self.recovery_dialog.update_status, "Cancelling recovery... cleaning up")
            
            def cleanup_thread():
                self.file_operations.cleanup_working_directory(self.working_dir)
                GLib.idle_add(self.recovery_dialog.update_status, "Recovery cancelled - cleanup complete")
            
            cleanup = threading.Thread(target=cleanup_thread, daemon=True)
            cleanup.start()
        
        return cancel_recovery
    
    def _run_recovery_thread(self, device_path, user_settings, is_image_file):
        try:
            destination_path = getattr(self.window, 'destination_path', None)
            keep_corrupted = user_settings.get("keep_corrupted", False)
            enable_logs = user_settings.get("save_logs", False)
            remove_duplicates = user_settings.get("remove_duplicates", False)
            save_image = user_settings.get("save_image", False)
            
            # Check there is enough space on destination for recovered files (and images if applicable)
            if not is_image_file and destination_path:
                is_sufficient, device_size, dest_available, dest_required = check_sufficient_space(
                    device_path, destination_path
                )
                if not is_sufficient:
                    content = "image and recovered files" if save_image else "recovered files"
                    self.logger.error(
                        f"Insufficient space at destination for {content}: need {dest_required:,} bytes "
                        f"but only {dest_available:,} bytes available at {destination_path}"
                    )
                    GLib.idle_add(
                        self.recovery_dialog.update_status,
                        f"Insufficient space at destination: need {self._format_bytes(dest_required)} "
                        f"but only {self._format_bytes(dest_available)} available"
                    )
                    return
            
            # Step 1: Create disk images (only for physical devices, not image files)
            if not is_image_file:
                GLib.idle_add(self.recovery_dialog.update_step_status, 'imaging', 'active')
                imaging_success = self.device_imager.setup_imager(device_path, self.working_dir)
                
                if not imaging_success:
                    if self.device_imager.cancelled:
                        self.logger.info("Disk imaging cancelled by user")
                        GLib.idle_add(self.recovery_dialog.update_step_status, 'imaging', 'error')
                        # Clean up incomplete image files
                        self.file_operations.cleanup_working_directory(self.working_dir)
                        return
                    self.logger.error("Disk imaging failed")
                    GLib.idle_add(self.recovery_dialog.update_step_status, 'imaging', 'error')
                    GLib.idle_add(self.recovery_dialog.update_status, "Recovery failed: Disk imaging unsuccessful")
                    # Clean up incomplete image files
                    self.file_operations.cleanup_working_directory(self.working_dir)
                    return
                
                GLib.idle_add(self.recovery_dialog.update_step_status, 'imaging', 'complete')
            else:
                self.logger.info(f"Using existing image file: {device_path}")
            
            # Step 2: Run PhotoRec to recover files from images
            GLib.idle_add(self.recovery_dialog.update_step_status, 'recovery', 'active')
            recovery_dir = os.path.join(self.working_dir, RECOVERED_FILES_DIR)
            
            # For image files, pass the file path directly to PhotoRec
            # For devices, use the working_dir where images were created
            recovery_source = device_path if is_image_file else self.working_dir
            recovery_success = self.photorec_recovery.setup_recovery(
                recovery_source, recovery_dir, keep_corrupted, enable_logs
            )
            
            if not recovery_success:
                if self.photorec_recovery.cancelled:
                    self.logger.info("PhotoRec recovery cancelled by user")
                    GLib.idle_add(self.recovery_dialog.update_step_status, 'recovery', 'error')
                    return
                self.logger.error("PhotoRec recovery failed")
                GLib.idle_add(self.recovery_dialog.update_step_status, 'recovery', 'error')
                GLib.idle_add(self.recovery_dialog.update_status, "Recovery failed: PhotoRec unsuccessful")
                return
            
            GLib.idle_add(self.recovery_dialog.update_step_status, 'recovery', 'complete')
            
            # Step 3: Remove duplicates if requested
            if remove_duplicates:
                GLib.idle_add(self.recovery_dialog.update_step_status, 'duplicates', 'active')
                GLib.idle_add(self.recovery_dialog.update_status, "Removing duplicate files")
                self.duplicate_remover.remove_duplicates(recovery_dir)
                GLib.idle_add(self.recovery_dialog.update_step_status, 'duplicates', 'complete')
            
            # Step 4: Organize recovered files by type
            GLib.idle_add(self.recovery_dialog.update_step_status, 'organize', 'active')
            GLib.idle_add(self.recovery_dialog.update_status, "Organizing files by type")
            self.file_operations.organize_recovered_files(recovery_dir, destination_path)
            GLib.idle_add(self.recovery_dialog.update_step_status, 'organize', 'complete')
            
            # Step 5: Move images if requested
            if destination_path and user_settings.get("save_image", False):
                GLib.idle_add(self.recovery_dialog.update_step_status, 'save_images', 'active')
                GLib.idle_add(self.recovery_dialog.update_status, "Saving disk images")
                self.file_operations.move_images_to_destination(self.working_dir, destination_path)
                GLib.idle_add(self.recovery_dialog.update_step_status, 'save_images', 'complete')
            
            # Step 6: Move logs if requested
            if destination_path and user_settings.get("save_logs", False):
                GLib.idle_add(self.recovery_dialog.update_step_status, 'save_logs', 'active')
                GLib.idle_add(self.recovery_dialog.update_status, "Saving logs")
                self.file_operations.move_logs_to_destination(self.working_dir, destination_path)
                GLib.idle_add(self.recovery_dialog.update_step_status, 'save_logs', 'complete')
            
            self.logger.info("Recovery completed successfully")
            GLib.idle_add(self.recovery_dialog.update_status, "Recovery complete")
            GLib.idle_add(self.recovery_dialog.mark_complete)
            
        except Exception as e:
            self.logger.error(f"Recovery failed with exception: {e}")
            self.logger.error(traceback.format_exc())
            GLib.idle_add(self.recovery_dialog.update_status, f"Recovery failed: {str(e)}")
            
            def show_error_dialog():
                error_dialog = Adw.AlertDialog.new("Recovery Failed", None)
                error_dialog.set_body(f"An error occurred during recovery:\n\n{str(e)}\n\nCheck logs for details.")
                error_dialog.add_response("ok", "OK")
                error_dialog.set_default_response("ok")
                error_dialog.present(self.window)
            
            GLib.idle_add(show_error_dialog)
    
    def _format_bytes(self, bytes_value):
        """Format bytes into human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
