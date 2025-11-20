# duplicates.py
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

import subprocess
import logging
import os
import shutil
from gi.repository import GLib
from .config import DUPLICATES_LOG

class DuplicateRemover:
    def __init__(self, recovery_dialog=None, working_dir=None):
        self.recovery_dialog = recovery_dialog
        self.working_dir = working_dir
        self.logger = logging.getLogger('datarecovery')
        self.current_process = None
        self.cancelled = False
    
    def remove_duplicates(self, recovery_dir):
        self.cancelled = False
        self.logger.info("=== Scanning For Duplicates ===")
        self.logger.info(f"Scanning for duplicates in: {recovery_dir}")
        
        if self.recovery_dialog:
            GLib.idle_add(self.recovery_dialog.update_status, "Removing duplicate files...")
        
        results_filename = DUPLICATES_LOG
        results_path = os.path.join(self.working_dir, results_filename)
        
        cmd = [
            "rdfind",
            "-deleteduplicates", "true",
            "-outputname", results_path,
            recovery_dir
        ]
        
        self.logger.info("Running rdfind to remove duplicates...")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.current_process = process
        
        stdout, stderr = process.communicate()
        
        self.current_process = None
        
        if self.cancelled:
            self.logger.info("rdfind was cancelled")
            return False
        
        if process.returncode == 0:
            self.logger.info("rdfind completed successfully - duplicates removed")
            return True
        else:
            self.logger.warning(f"rdfind failed with return code {process.returncode}")
            if stderr:
                self.logger.warning(f"rdfind error: {stderr}")
            return False

    def cancel(self):
        self.cancelled = True
        if self.current_process:
            self.logger.info("Terminating rdfind process")
            try:
                self.current_process.terminate()
                # Give it a moment to terminate gracefully
                try:
                    self.current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # If it doesn't terminate, kill it
                    self.current_process.kill()
            except Exception as e:
                self.logger.error(f"Failed to terminate rdfind process: {e}")

