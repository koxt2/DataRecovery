# Copyright 2025 Richard Potts
# SPDX-License-Identifier: GPL-2.0-or-later

import logging
import os
import re
import subprocess

from gi.repository import GLib

from .block_devices import check_sufficient_space
from .config import (
    DISK_SPACE_SAFETY_MARGIN_PERCENT,
    IMAGE_FILE_EXTENSION,
    MAP_FILE_EXTENSION,
)
from .log import setup_imager_logging
from .utils import format_bytes


class DeviceImager:
    def __init__(self, recovery_dialog=None):
        self.recovery_dialog = recovery_dialog
        self.logger = logging.getLogger("datarecovery")
        self.imager_logger = logging.getLogger("imager_logger")
        self.current_process = None
        self.cancelled = False

    def run_imager(self, device_path, image_path, mapfile_path):
        self.cancelled = False

        process = subprocess.Popen(
            [
                "pkexec",
                "datarecovery-pkexec-helper",
                device_path,
                image_path,
                mapfile_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        self.current_process = process

        try:
            for line in process.stdout:
                if self.cancelled:
                    self.logger.info("Imager cancelled by user")
                    try:
                        process.terminate()
                    except OSError:
                        pass
                    break

                self.imager_logger.info(f"Output: {line.strip()}")

                device_name = device_path.replace("/dev/", "")
                if self.recovery_dialog:
                    GLib.idle_add(
                        self.recovery_dialog.update_status,
                        f"Creating image of {device_name}",
                    )

                # Extract and display percentage
                pct_match = re.search(r"pct rescued:\s+(\d+\.\d+)%", line)
                if pct_match:
                    percentage = float(pct_match.group(1))

                    if self.recovery_dialog:
                        GLib.idle_add(self.recovery_dialog.update_progress, percentage / 100.0)

            return_code = process.wait()

            if self.cancelled:
                self.logger.info("Imager was cancelled")
                return False

            if return_code != 0:
                self.logger.error(f"ddrescue helper failed with exit code {return_code}")
                return False

            self.logger.info("Image creation completed successfully")
            return True
        finally:
            self.current_process = None

    def setup_imager(self, device_path, working_dir):
        self.logger.info("Setting up ddrescue")
        setup_imager_logging(working_dir)

        # Check if there's sufficient disk space before starting
        is_sufficient, device_size, available_space, required_space = check_sufficient_space(
            device_path, working_dir, DISK_SPACE_SAFETY_MARGIN_PERCENT
        )

        if not is_sufficient:
            self.logger.error(
                f"Insufficient disk space: need {required_space:,} bytes but only {available_space:,} bytes available"
            )
            if self.recovery_dialog:
                GLib.idle_add(
                    self.recovery_dialog.update_status,
                    f"Insufficient disk space: need {format_bytes(required_space)} but only {format_bytes(available_space)} available",
                )
            return False

        self.logger.info(
            f"Disk space check passed: {available_space:,} bytes available, {required_space:,} bytes required for {device_size:,} byte device"
        )

        safe_name = device_path.replace("/dev/", "").replace("/", "_")
        image_path = os.path.join(working_dir, f"{safe_name}{IMAGE_FILE_EXTENSION}")
        mapfile_path = os.path.join(working_dir, f"{safe_name}_mapfile{MAP_FILE_EXTENSION}")

        self.logger.info(f"Device: {device_path}")
        self.logger.info(f"Image: {image_path}")
        self.logger.info(f"Mapfile: {mapfile_path}")
        self.logger.info("Running ddrescue")

        success = self.run_imager(device_path, image_path, mapfile_path)

        if success:
            self.logger.info(f"Image creation completed and saved to {working_dir}")

        return success

    def cancel(self):
        self.cancelled = True
        self.logger.info("Cancellation requested - stopping ddrescue")

        try:
            subprocess.run(["pkexec", "pkill", "-9", "ddrescue"], capture_output=True, text=True)
            self.logger.info("Sent kill signal to all ddrescue processes")
        except Exception as e:
            self.logger.warning(f"Could not kill ddrescue: {e}")

        if self.current_process:
            try:
                self.current_process.terminate()
            except Exception as e:
                self.logger.debug(f"Could not terminate pkexec wrapper: {e}")
