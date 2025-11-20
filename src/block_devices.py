# block_devices.py
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

from gi.repository import Gio
import subprocess
import json
import logging
import os

logger = logging.getLogger('datarecovery')

class DeviceMonitor:
    def __init__(self, device_dropdown):
        self.device_dropdown = device_dropdown
        self.start_monitor()
    
    def start_monitor(self):
        try:
            self.connection = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
            
            for signal_name in ['InterfacesAdded', 'InterfacesRemoved']:
                self.connection.signal_subscribe(
                    'org.freedesktop.UDisks2',
                    'org.freedesktop.DBus.ObjectManager',
                    signal_name,
                    None, None,
                    Gio.DBusSignalFlags.NONE,
                    self._on_device_change,
                    None
                )
            
            logger.info("Device monitor started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start device monitor: {e}")
            return False
    
    def _on_device_change(self, *args):
        self.device_dropdown.refresh_with_selection_preserved()

def get_block_devices():
    try:
        result = subprocess.run([
            'lsblk', '-J', '-o', 
            'NAME,PATH,SIZE,FSTYPE,LABEL,MOUNTPOINT,MODEL,SERIAL,TYPE,UUID,PARTUUID,PARTTYPE'
        ], capture_output=True, text=True, check=True)

        data = json.loads(result.stdout)
        devices, partitions = [], []

        def process_device(device_data):
            info = {
                'path': device_data.get('path', ''),
                'model': device_data.get('model', ''),
                'serial': device_data.get('serial', ''),
                'size': _parse_size(device_data.get('size', '0')),
                'id_type': device_data.get('fstype', ''),
                'label': device_data.get('label', ''),
                'mounted': bool(device_data.get('mountpoint')),
                'mount_path': device_data.get('mountpoint'),
                'uuid': device_data.get('uuid', ''),
                'partuuid': device_data.get('partuuid', ''),
                'parttype': device_data.get('parttype', '')
            }

            if device_data.get('type') == 'disk':
                devices.append(info)
            elif device_data.get('type') == 'part':
                partitions.append(info)

            # Process children (partitions)
            for child in device_data.get('children', []):
                process_device(child)

        for device in data['blockdevices']:
            process_device(device)
        
        return devices, partitions

    except Exception as e:
        logger.error(f"Failed to get block devices via lsblk: {e}")
        return [], []

def _parse_size(size_str):
    """Convert lsblk size string to bytes"""
    if not size_str:
        return 0

    multipliers = {'B': 1, 'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4, 'P': 1024**5}

    # Handle cases like '0B', '1.5G', etc.
    size_str = str(size_str).strip().upper()
    
    if not size_str:
        return 0
    
    # Check if last character is a unit
    if size_str[-1] in multipliers:
        unit = size_str[-1]
        number_part = size_str[:-1]
        
        try:
            number = float(number_part)
            return int(number * multipliers[unit])
        except (ValueError, OverflowError) as e:
            logger.warning(f"Could not parse size '{size_str}': {e}")
            return 0
    
    # Handle plain numbers (assume bytes)
    try:
        return int(float(size_str))
    except (ValueError, OverflowError) as e:
        logger.warning(f"Could not parse size '{size_str}': {e}")
        return 0

def get_device_size(device_path):
    try:
        result = subprocess.run(
            ['lsblk', '-b', '-n', '-o', 'SIZE', device_path],
            capture_output=True,
            text=True,
            check=True
        )
        size_str = result.stdout.strip()
        return int(size_str)
    except (subprocess.CalledProcessError, ValueError) as e:
        logger.error(f"Failed to get device size for {device_path}: {e}")
        return 0

def get_available_space(directory_path):
    try:
        stat = os.statvfs(directory_path)
        # Available space = fragment size * available fragments
        available_bytes = stat.f_bavail * stat.f_frsize
        return available_bytes
    except OSError as e:
        logger.error(f"Failed to get available space for {directory_path}: {e}")
        return 0

def check_sufficient_space(device_path, destination_dir, safety_margin_percent=0.10):
    device_size = get_device_size(device_path)
    available_space = get_available_space(destination_dir)
    
    if device_size == 0:
        logger.warning(f"Could not determine device size for {device_path}")
        # If size cannot be determined, assume it's okay (fail open for edge cases)
        return (True, 0, available_space, 0)
    
    margin = int(device_size * safety_margin_percent)
    required_space = device_size + margin
    
    is_sufficient = available_space >= required_space
    
    logger.info(f"Disk space check: device={device_size:,} bytes, available={available_space:,} bytes, required={required_space:,} bytes")
    
    return (is_sufficient, device_size, available_space, required_space)

