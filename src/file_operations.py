# file_operations.py
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
import shutil
import subprocess
import logging
from gi.repository import GLib
from .config import RECOVERY_DATA_FOLDER, IMAGE_FILE_EXTENSION, MAP_FILE_EXTENSION, LOG_FILE_EXTENSION, DATARECOVERY_LOG

class FileOperations:
    def __init__(self, recovery_dialog=None):
        self.recovery_dialog = recovery_dialog
        self.logger = logging.getLogger('datarecovery')

    def cleanup_working_directory(self, working_dir):
        self.logger.info("Cleaning up working directory after cancellation")
        
        if not os.path.exists(working_dir):
            self.logger.warning(f"Working directory does not exist: {working_dir}")
            return True  # Nothing to clean up
        
        main_log = os.path.join(working_dir, DATARECOVERY_LOG)
        
        items_removed = 0
        items_failed = 0
        
        items = os.listdir(working_dir)
        
        for item in items:
            item_path = os.path.join(working_dir, item)
            
            # Skip the main datarecovery.log
            if item_path == main_log:
                self.logger.info(f"Preserving {DATARECOVERY_LOG}")
                continue
            
            # Remove everything else
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.remove(item_path)
                    self.logger.debug(f"Removed file: {item}")
                    items_removed += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    self.logger.debug(f"Removed directory: {item}")
                    items_removed += 1
            except OSError as e:
                self.logger.error(f"Failed to remove {item}: {e}")
                items_failed += 1
        
        self.logger.info(f"Working directory cleanup complete: {items_removed} removed, {items_failed} failed")
        return items_failed == 0

    def move_images_to_destination(self, working_dir, destination_dir):
        self.logger.info(f"Moving images from {working_dir} to {destination_dir}")
        
        app_data_dir = os.path.join(destination_dir, RECOVERY_DATA_FOLDER)
        os.makedirs(app_data_dir, exist_ok=True)
        
        files_moved = 0
        files_failed = 0
        
        files = os.listdir(working_dir)
        
        for filename in files:
            if filename.endswith((IMAGE_FILE_EXTENSION, MAP_FILE_EXTENSION)):
                source_path = os.path.join(working_dir, filename)
                dest_path = os.path.join(app_data_dir, filename)
                
                try:
                    shutil.move(source_path, dest_path)
                    files_moved += 1
                    self.logger.info(f"Moved {filename} to destination")
                except OSError as e:
                    self.logger.error(f"Failed to move {filename}: {e}")
                    files_failed += 1
        
        if files_moved == 0 and files_failed == 0:
            self.logger.warning("No image or map files found to move")
        else:
            self.logger.info(f"Image move complete: {files_moved} moved, {files_failed} failed to {app_data_dir}")
        
        return files_failed == 0

    def move_logs_to_destination(self, working_dir, destination_dir):
        app_data_dir = os.path.join(destination_dir, RECOVERY_DATA_FOLDER)
        os.makedirs(app_data_dir, exist_ok=True)
        
        logs_processed = 0
        
        files = os.listdir(working_dir)
        
        for filename in files:
            if filename.endswith(LOG_FILE_EXTENSION):
                source_path = os.path.join(working_dir, filename)
                dest_path = os.path.join(app_data_dir, filename)
                
                # Copy datarecovery.log, move all others
                if filename == DATARECOVERY_LOG:
                    shutil.copy2(source_path, dest_path)
                    self.logger.info(f"Copied {filename} to destination")
                else:
                    shutil.move(source_path, dest_path)
                    self.logger.info(f"Moved {filename} to destination")
                logs_processed += 1
        
        if logs_processed == 0:
            self.logger.warning("No log files found")
        else:
            self.logger.info(f"Processed {logs_processed} log files to {app_data_dir}")
        
        return True

    def organize_recovered_files(self, recovery_dir, destination_dir):
        self.logger.info("Organizing recovered files by type")
        
        if self.recovery_dialog:
            GLib.idle_add(self.recovery_dialog.update_status, "Organizing recovered files")
        
        self._organize_corrupted_files(recovery_dir, destination_dir)
        
        extensions = self._get_all_extensions(recovery_dir)
        
        if not extensions:
            self.logger.warning("No files found to organize")
            return False
        
        self.logger.info(f"Found {len(extensions)} different file types")
        
        failed_extensions = []
        for ext in extensions:
            if not self._organize_by_extension(recovery_dir, destination_dir, ext):
                failed_extensions.append(ext)
        
        if not self._organize_files_without_extension(recovery_dir, destination_dir):
            self.logger.warning("Failed to organize some files without extensions")
        
        if failed_extensions:
            self.logger.warning(f"Failed to organize files with extensions: {', '.join(failed_extensions)}")
            return False
        
        self.logger.info("File organization completed successfully")
        return True

    def _get_all_extensions(self, recovery_dir):
        extensions = set()
        
        for root, dirs, files in os.walk(recovery_dir):
            for file in files:
                if '.' in file and not file.startswith('.'):
                    ext = os.path.splitext(file)[1][1:].lower()
                    if ext:
                        extensions.add(ext)
        
        return sorted(extensions)

    def _organize_corrupted_files(self, source_dir, dest_dir):
        corrupted_dir = os.path.join(dest_dir, "corrupted")
        os.makedirs(corrupted_dir, exist_ok=True)
        
        corrupted_count = 0
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.startswith('b'):
                    src_path = os.path.join(root, file)
                    dest_path = os.path.join(corrupted_dir, file)
                    
                    os.rename(src_path, dest_path)
                    corrupted_count += 1
        
        if corrupted_count > 0:
            self.logger.info(f"Moved {corrupted_count} corrupted files to corrupted directory")
        else:
            try:
                os.rmdir(corrupted_dir)
            except:
                pass
        
        return True

    def _organize_by_extension(self, source_dir, dest_dir, extension):
        ext_dir = os.path.join(dest_dir, extension)
        os.makedirs(ext_dir, exist_ok=True)
        
        try:
            subprocess.run(
                ['find', source_dir, '-name', f'*.{extension}', '-type', 'f', '-exec', 'mv', '{}', f'{ext_dir}/', ';'],
                check=True, capture_output=True, text=True, timeout=300
            )
            self.logger.info(f"Organized .{extension} files")
            return True
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout while organizing .{extension} files (> 5 minutes)")
            return False
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to organize .{extension} files (exit code {e.returncode}): {e.stderr}")
            return False

    def _organize_files_without_extension(self, source_dir, dest_dir):
        no_ext_dir = os.path.join(dest_dir, "no_extension")
        os.makedirs(no_ext_dir, exist_ok=True)
        
        files_moved = 0
        
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if '.' not in file or file.startswith('.'):
                    src_path = os.path.join(root, file)
                    dest_path = os.path.join(no_ext_dir, file)
                    
                    os.rename(src_path, dest_path)
                    files_moved += 1
        
        self.logger.info(f"Organized files without extension: {files_moved} moved")
        return True
