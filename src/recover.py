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
import re
import subprocess
import logging
import shutil
import time
import threading
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

    def setup_recovery(self, source, recovery_dir, keep_corrupted=False):
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
        
        if not self._scan_image_file(image_file, recovery_dir, keep_corrupted):
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

    def _scan_image_file(self, image_file, recovery_dir, keep_corrupted):
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
        
        cmd = [
            "photorec",
            "/log",  # Always enable logging for progress tracking
            "/d", output_dir,
            "/cmd", image_file,
            options
        ]
        
        self.logger.info(f"Running command: {' '.join(cmd)}")
        
        cwd = os.path.dirname(output_dir) or output_dir
        if not os.path.exists(cwd):
            cwd = os.getcwd()
        self.logger.info(f"Running PhotoRec with cwd={cwd}")
        
        # Determine log file path (PhotoRec writes to cwd/photorec.log when /log flag is used)
        log_file_path = os.path.join(cwd, "photorec.log")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd
        )
        
        self.current_process = process
        
        # Start log monitoring in a separate thread
        monitor_data = {'stop': False, 'process': process}
        monitor_thread = threading.Thread(
            target=self._monitor_photorec_log,
            args=(log_file_path, filename, monitor_data),
            daemon=True
        )
        monitor_thread.start()
        
        # Wait for process to complete
        process.wait()
        
        # Signal monitoring to finish up and wait for it
        monitor_data['stop'] = True
        monitor_thread.join(timeout=3)
        
        # Ensure we reach 100% when recovery completes successfully
        if process.returncode == 0 and self.recovery_dialog:
            GLib.idle_add(self.recovery_dialog.update_progress, 1.0)
        
        self.current_process = None
        
        if self.cancelled:
            self.logger.info("PhotoRec was cancelled")
            return False
        
        # Move PhotoRec log to working directory
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

    def _monitor_photorec_log(self, log_file_path, filename, monitor_data):
        """Monitor PhotoRec's log file to track progress"""
        file_count = 0
        max_sector = 0
        total_sectors = None
        last_progress_update = 0
        found_completion = False
        
        # Wait for log file to be created
        wait_time = 0
        while not os.path.exists(log_file_path) and wait_time < 5:
            if monitor_data['stop']:
                return
            time.sleep(0.1)
            wait_time += 0.1
        
        if not os.path.exists(log_file_path):
            self.logger.warning("PhotoRec log not created, progress unavailable")
            return
        
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as log_file:
                while not found_completion:
                    line = log_file.readline()
                    if not line:
                        # No more data available right now
                        if monitor_data['stop']:
                            # Process has finished, read any remaining lines
                            remaining = log_file.read()
                            if remaining:
                                # Process remaining lines
                                for remaining_line in remaining.split('\n'):
                                    if remaining_line.strip():
                                        file_count, max_sector, total_sectors, last_progress_update, found = \
                                            self._parse_log_line(remaining_line, filename, 
                                                               file_count, max_sector, total_sectors, last_progress_update)
                                        if found:
                                            found_completion = True
                                            break
                            break
                        # Wait a bit for more data
                        time.sleep(0.05)
                        continue
                    
                    file_count, max_sector, total_sectors, last_progress_update, found = \
                        self._parse_log_line(line, filename, file_count, max_sector, total_sectors, last_progress_update)
                    if found:
                        found_completion = True
        except Exception as e:
            self.logger.warning(f"Error monitoring PhotoRec progress: {e}")

    def _parse_log_line(self, line, filename, file_count, max_sector, total_sectors, last_progress_update):
        """Parse a single log line and update progress. Returns updated values and completion flag."""
        found_completion = False
        
        # Parse partition size from any primary partition line (e.g. "P ext4", "P MS Data", "P Linux")
        # Format: "   P ext4                     0   0  1  1869 101 24   30031872"
        # The last number is the total sector count.
        if not total_sectors and re.match(r'\s+P\s+\w', line):
            numbers = re.findall(r'\d+', line)
            if numbers:
                candidate = int(numbers[-1])
                if candidate > 0:
                    total_sectors = candidate
                    self.logger.info(f"Partition has {total_sectors:,} sectors for progress calculation")
        
        # Parse recovered file lines to track progress
        # Format: "/path/to/file.ext    XXXX-YYYY" 
        file_match = re.search(r'/[^\s]+\.[\w]+[\s\t]+(\d+)-(\d+)', line)
        if file_match:
            file_count += 1
            end_sector = int(file_match.group(2))
            
            if end_sector > max_sector:
                max_sector = end_sector
                
                # Calculate progress: (offset / partition_size) * 100
                if total_sectors and total_sectors > 0:
                    progress = min(float(max_sector) / float(total_sectors), 1.0)
                    
                    # Only update if progress changed significantly (every 1%)
                    if int(progress * 100) > last_progress_update:
                        last_progress_update = int(progress * 100)
                        if self.recovery_dialog:
                            GLib.idle_add(self.recovery_dialog.update_progress, progress)
            
            # Update file count every 10 files
            if file_count % 10 == 0 and self.recovery_dialog:
                GLib.idle_add(
                    self.recovery_dialog.update_status,
                    f"Recovering from {filename} - {file_count} files found"
                )
        
        # Parse completion message: "Total: NNN files found"
        if 'Total:' in line and 'files found' in line:
            total_match = re.search(r'Total:\s+(\d+)\s+files? found', line)
            if total_match:
                file_count = int(total_match.group(1))
                self.logger.info(f"PhotoRec completed: {file_count} total files recovered")
                if self.recovery_dialog:
                    GLib.idle_add(self.recovery_dialog.update_progress, 1.0)
                    GLib.idle_add(
                        self.recovery_dialog.update_status,
                        f"Completed: {file_count} files recovered from {filename}"
                    )
                found_completion = True
        
        return (file_count, max_sector, total_sectors, last_progress_update, found_completion)

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

