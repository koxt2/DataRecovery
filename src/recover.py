# recover.py
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
import subprocess
import logging
import shutil
from gi.repository import GLib
from .config import (
    IMAGE_FILE_EXTENSION, 
    PHOTOREC_LOG_PREFIX, 
    PHOTOREC_OPTIONS_BASE,
    PHOTOREC_OPTION_KEEP_CORRUPTED,
    PHOTOREC_OPTION_SEARCH,
)

class DeviceRecovery:
    def __init__(self, recovery_dialog=None):
        self.recovery_dialog = recovery_dialog
        self.logger = logging.getLogger('datarecovery')
        self.current_process = None
        self.cancelled = False

    def setup_recovery(self, source, recovery_dir, keep_corrupted=False, enable_logs=False):
        self.logger.info("Starting PhotoRec recovery")
        self.cancelled = False
        
        # Check if source is a file or directory
        if os.path.isfile(source):
            # It's a single image file - scan it directly
            image_file = source
            self.working_dir = os.path.dirname(recovery_dir)
            self.logger.info(f"Scanning single image file: {source}")
        else:
            # It's a directory - find the single .img file in it
            self.working_dir = source
            image_file = self._find_image_file(source)
            
            if not image_file:
                self.logger.error("No image file found to scan")
                return False
            
            self.logger.info(f"Found image file: {image_file}")
        
        os.makedirs(recovery_dir, exist_ok=True)
        
        if self.cancelled:
            self.logger.info("PhotoRec cancelled by user")
            return False
        
        if not self._scan_image_file(image_file, recovery_dir, keep_corrupted, enable_logs):
            if self.cancelled:
                return False
            self.logger.error(f"Scan of {image_file} failed")
            return False
        
        self.logger.info("PhotoRec recovery completed")
        return True

    def _find_image_file(self, working_dir):
        if not os.path.isdir(working_dir):
            return None
        
        for filename in os.listdir(working_dir):
            if filename.endswith(IMAGE_FILE_EXTENSION):
                full_path = os.path.join(working_dir, filename)
                self.logger.info(f"Found image file: {filename}")
                return full_path
        
        return None

    def _scan_image_file(self, image_file, recovery_dir, keep_corrupted, enable_logs):
        if not os.path.exists(image_file):
            self.logger.error(f"Image file does not exist: {image_file}")
            return False
            
        filename = os.path.basename(image_file)
        name_without_ext = os.path.splitext(filename)[0]
        
        self.logger.info(f"Scanning {filename}")
        
        if self.recovery_dialog:
            GLib.idle_add(self.recovery_dialog.update_status, f"Recovering files from {filename}")
        
        output_dir = os.path.join(recovery_dir, name_without_ext)
        os.makedirs(output_dir, exist_ok=True)
        
        options = PHOTOREC_OPTIONS_BASE
        if keep_corrupted:
            options += f",{PHOTOREC_OPTION_KEEP_CORRUPTED}"
        
        options += f",{PHOTOREC_OPTION_SEARCH}"
        
        cmd = ["photorec"]
        
        if enable_logs:
            cmd.append("/log")
        
        cmd.extend([
            "/d", output_dir,
            "/cmd", image_file,
            options
        ])
        
        self.logger.info(f"Running command: {' '.join(cmd)}")
        
        cwd = os.path.dirname(output_dir) or output_dir
        if not os.path.exists(cwd):
            cwd = os.getcwd()
        self.logger.info(f"Running PhotoRec with cwd={cwd}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd
        )
        
        self.current_process = process
        
        stdout, stderr = process.communicate()
        
        self.current_process = None
        
        if self.cancelled:
            self.logger.info("PhotoRec was cancelled")
            return False
        
        if stderr:
            self.logger.warning(f"PhotoRec warnings for {filename}: {stderr}")
        
        if enable_logs:
            log_source = os.path.join(cwd, "photorec.log")
            if os.path.exists(log_source):
                log_dest = os.path.join(self.working_dir, f"{PHOTOREC_LOG_PREFIX}{name_without_ext}.log")
                try:
                    shutil.move(log_source, log_dest)
                    self.logger.info(f"Moved PhotoRec log to {log_dest}")
                except (OSError, shutil.Error) as e:
                    self.logger.warning(f"Failed to move PhotoRec log: {e}")
        
        if process.returncode == 0:
            self.logger.info(f"PhotoRec scan of {filename} completed successfully")
            return True
        else:
            self.logger.error(f"PhotoRec scan of {filename} failed with exit code {process.returncode}")
            return False

    def cancel(self):
        self.cancelled = True
        if self.current_process:
            self.logger.info("Terminating PhotoRec process")
            try:
                self.current_process.terminate()
                # Give it a moment to terminate gracefully
                try:
                    self.current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # If it doesn't terminate, kill it
                    self.current_process.kill()
            except Exception as e:
                self.logger.error(f"Failed to terminate PhotoRec process: {e}")

