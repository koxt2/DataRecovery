# mounted_check.py
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
from gi.repository import Adw, GLib
from . import block_devices

class MountedPartitionChecker:
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.logger = logging.getLogger('datarecovery')
    
    def check_and_handle_mounted_partitions(self, device_path, success_callback):
        self.logger.info(f"Checking for mounted devices/partitions on device: {device_path}")
        
        devices, partitions = block_devices.get_block_devices()
        
        all_block_devices = devices + partitions
        
        mounted_partitions = []
        
        for block_device in all_block_devices:
            if ((block_device['path'] == device_path or block_device['path'].startswith(device_path)) and 
                block_device.get('mounted', False) and 
                block_device.get('mount_path')):
                
                mount_path = block_device['mount_path']
                
                # Check if this is a system partition
                # Exclude removable media mount points: /run/media, /media, /mnt
                is_system_partition = (
                    mount_path.startswith('/') and 
                    not mount_path.startswith('/run/media/') and
                    not mount_path.startswith('/media/') and
                    not mount_path.startswith('/mnt/')
                )
                
                if is_system_partition:
                    self.logger.error(f"Host system partition detected: {block_device['path']} mounted at {mount_path}")
                    self.logger.error(f"Cannot recover from devices that are part of the running system")
                    self._show_system_device_error(block_device['path'], mount_path)
                    return False
                
                device_type = "device" if block_device['path'] == device_path else "partition"
                self.logger.warning(f"Found mounted {device_type}: {block_device['path']} → {mount_path}")
                mounted_partitions.append({
                    'path': block_device['path'],
                    'mount_path': mount_path
                })
        
        if not mounted_partitions:
            self.logger.info("No mounted devices/partitions found, proceeding with recovery")
            success_callback()
            return True
        
        self._show_unmount_dialog(mounted_partitions, device_path, success_callback)
        return False
    
    def _show_unmount_dialog(self, mounted_partitions, device_path, success_callback):
        self.logger.info("Displaying unmount dialog to user")
        for partition in mounted_partitions:
            self.logger.info(f"  - {partition['path']} mounted at {partition['mount_path']}")
        
        partition_list = "\n".join([f"• {p['path']} → {p['mount_path']}" for p in mounted_partitions])
        
        dialog = Adw.AlertDialog.new("Mounted Partitions Detected", None)
        
        body_text = f"The following partitions are currently mounted:\n\n{partition_list}\n\nUnmounting recommended before creating disk images."
        dialog.set_body(body_text)
        
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("continue", "Continue Anyway")
        dialog.add_response("unmount", "Unmount & Continue")
        
        dialog.set_response_appearance("unmount", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        
        dialog.set_default_response("unmount")
        dialog.set_close_response("cancel")
        
        def on_response(dialog, response):
            self.logger.info(f"User selected dialog response: {response}")
            
            if response == "unmount":
                success = True
                failed_partitions = []
                for partition in mounted_partitions:
                    if not self._unmount_partition(partition['path']):
                        success = False
                        failed_partitions.append(partition['path'])
                
                if success:
                    self.logger.info("All partitions unmounted successfully, proceeding with recovery")
                    GLib.idle_add(success_callback)
                else:
                    self.logger.error(f"Failed to unmount partitions: {failed_partitions}")
                    GLib.idle_add(lambda: self._show_unmount_failure_dialog(failed_partitions))
            elif response == "continue":
                self.logger.warning("User chose to continue with mounted partitions - this may cause data corruption")
                GLib.idle_add(success_callback)
            else:  # cancel
                self.logger.info("User cancelled recovery due to mounted partitions")
        
        dialog.connect("response", on_response)
        dialog.present(self.parent_window)
    
    def _show_unmount_failure_dialog(self, failed_partitions):
        self.logger.info("Displaying unmount failure dialog to user")
        
        partition_list = "\n".join([f"• {p}" for p in failed_partitions])
        
        error_dialog = Adw.AlertDialog.new("Unmount Failed", None)
        
        body_text = f"Failed to unmount the following partitions:\n\n{partition_list}\n\nYou may need to close applications using these partitions or unmount them manually before proceeding with recovery."
        error_dialog.set_body(body_text)
        
        error_dialog.add_response("ok", "OK")
        error_dialog.set_response_appearance("ok", Adw.ResponseAppearance.DEFAULT)
        error_dialog.set_default_response("ok")
        error_dialog.set_close_response("ok")
        
        error_dialog.present(self.parent_window)
    
    def _show_system_device_error(self, device_path, mount_path):
        """Show an error dialog when user tries to scan a system device"""
        self.logger.info("Displaying system device error dialog to user")
        
        error_dialog = Adw.AlertDialog.new("System Device Detected", None)
        
        body_text = f"The selected device contains a partition mounted at:\n\n{mount_path}\n\nThis appears to be part of your running system. Data recovery cannot be performed on the system drive while it's in use.\n\nTo recover data from this device:\n1. Boot from a live USB/CD\n2. Run this application from the live environment\n3. Select this device for recovery"
        error_dialog.set_body(body_text)
        
        error_dialog.add_response("ok", "OK")
        error_dialog.set_response_appearance("ok", Adw.ResponseAppearance.DEFAULT)
        error_dialog.set_default_response("ok")
        error_dialog.set_close_response("ok")
        
        error_dialog.present(self.parent_window)
    
    def _unmount_partition(self, partition_path):
        self.logger.info(f"Attempting to unmount partition: {partition_path}")
        try:
            result = subprocess.run(
                ["udisksctl", "unmount", "-b", partition_path],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                self.logger.info(f"Successfully unmounted {partition_path}")
                return True
            else:
                self.logger.error(f"Failed to unmount {partition_path}: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Exception while unmounting {partition_path}: {e}")
            print(f"Exception unmounting {partition_path}: {e}")
            return False
