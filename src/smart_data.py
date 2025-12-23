# smart_data.py
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

import logging
from gi.repository import Gio, GLib

from . import config

logger = logging.getLogger('datarecovery')

def get_smart_status(device_path):
    try:
        connection = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        device_name = device_path.replace('/dev/', '')
        block_path = f'/org/freedesktop/UDisks2/block_devices/{device_name}'
        
        logger.info(f"Attempting to get SMART data via UDisks2 for {device_path}")
        
        # Get drive object path
        drive_variant = connection.call_sync(
            'org.freedesktop.UDisks2', block_path, 'org.freedesktop.DBus.Properties', 'Get',
            GLib.Variant('(ss)', ('org.freedesktop.UDisks2.Block', 'Drive')),
            GLib.VariantType('(v)'), Gio.DBusCallFlags.NONE, 5000, None
        )
        drive_path = drive_variant.unpack()[0]
        
        if drive_path == '/':
            logger.info(f"No drive object for {device_path}")
            return 'unavailable', {}
        
        logger.info(f"Found drive object: {drive_path}")
        
        # Is drive nvme or ata?
        is_nvme = 'nvme' in device_path.lower()
        return _get_smart_nvme(connection, drive_path, device_path) if is_nvme else _get_smart_ata(connection, drive_path, device_path)
        
    except Exception as e:
        logger.warning(f"Could not get SMART via UDisks2 for {device_path}: {e}")
        return 'unavailable', {}

def _get_smart_ata(connection, drive_path, device_path):
    try:
        interface = 'org.freedesktop.UDisks2.Drive.Ata'
        
        # Check if SMART is supported
        smart_supported = connection.call_sync(
            'org.freedesktop.UDisks2', drive_path, 'org.freedesktop.DBus.Properties', 'Get',
            GLib.Variant('(ss)', (interface, 'SmartSupported')),
            GLib.VariantType('(v)'), Gio.DBusCallFlags.NONE, 5000, None
        ).unpack()[0]
        
        if not smart_supported:
            logger.info(f"SMART not supported for {device_path}")
            return 'unavailable', {}
        
        # Get health status
        smart_failing = connection.call_sync(
            'org.freedesktop.UDisks2', drive_path, 'org.freedesktop.DBus.Properties', 'Get',
            GLib.Variant('(ss)', (interface, 'SmartFailing')),
            GLib.VariantType('(v)'), Gio.DBusCallFlags.NONE, 5000, None
        ).unpack()[0]
        
        # Get temperature
        temp_kelvin = connection.call_sync(
            'org.freedesktop.UDisks2', drive_path, 'org.freedesktop.DBus.Properties', 'Get',
            GLib.Variant('(ss)', (interface, 'SmartTemperature')),
            GLib.VariantType('(v)'), Gio.DBusCallFlags.NONE, 5000, None
        ).unpack()[0]
        
        # Get power-on time
        power_on_seconds = connection.call_sync(
            'org.freedesktop.UDisks2', drive_path, 'org.freedesktop.DBus.Properties', 'Get',
            GLib.Variant('(ss)', (interface, 'SmartPowerOnSeconds')),
            GLib.VariantType('(v)'), Gio.DBusCallFlags.NONE, 5000, None
        ).unpack()[0]
        
        # Get detailed attributes
        attributes_variant = connection.call_sync(
            'org.freedesktop.UDisks2', drive_path, interface, 'SmartGetAttributes',
            GLib.Variant('(a{sv})', ({},)),
            GLib.VariantType('(a(ysqiiixia{sv}))'), Gio.DBusCallFlags.NONE, 10000, None
        )
        
        ata_attributes = []
        for attr in attributes_variant.unpack()[0]:
            ata_attributes.append({
                'id': attr[0],
                'name': attr[1].replace('-', '_'),
                'value': attr[3],
                'worst': attr[4],
                'thresh': attr[5],
                'raw': {'value': attr[6]},
                'when_failed': ''
            })
        
        data = {
            'temperature': {'current': int(temp_kelvin - 273.15)},
            'power_on_time': {'hours': power_on_seconds // 3600},
            'smart_status': {'passed': not smart_failing},
            'ata_smart_attributes': {'table': ata_attributes}
        }
        
        # Determine status based on SmartFailing and attribute analysis
        if smart_failing:
            status = 'failing'
        else:
            status = 'healthy'
            # Check for warning conditions using CRITICAL_ATTRIBUTES from config
            for attr in ata_attributes:
                attr_id = attr['id']
                raw_value = attr['raw']['value']
                
                # Check if this attribute is critical and exceeds its threshold
                if attr_id in config.CRITICAL_ATTRIBUTES:
                    attr_name, threshold = config.CRITICAL_ATTRIBUTES[attr_id]
                    if raw_value > threshold:
                        status = 'warning'
                        logger.info(f"Attribute {attr_id} ({attr_name}) exceeds threshold: {raw_value} > {threshold}")
                        break  # One warning is enough
        
        logger.info(f"Got SMART data for {device_path} via UDisks2 ATA: {int(temp_kelvin - 273.15)}°C, {power_on_seconds // 3600}h, {len(ata_attributes)} attrs, status={status}")
        return status, data
        
    except Exception as e:
        logger.warning(f"Could not get SMART via UDisks2 ATA for {device_path}: {e}")
        return 'unavailable', {}

def _get_smart_nvme(connection, drive_path, device_path):
    try:
        interface = 'org.freedesktop.UDisks2.NVMe.Controller'
        
        # Get health status
        critical_warnings = connection.call_sync(
            'org.freedesktop.UDisks2', drive_path, 'org.freedesktop.DBus.Properties', 'Get',
            GLib.Variant('(ss)', (interface, 'SmartCriticalWarning')),
            GLib.VariantType('(v)'), Gio.DBusCallFlags.NONE, 5000, None
        ).unpack()[0]

        # Get temperature 
        temp_kelvin = connection.call_sync(
            'org.freedesktop.UDisks2', drive_path, 'org.freedesktop.DBus.Properties', 'Get',
            GLib.Variant('(ss)', (interface, 'SmartTemperature')),
            GLib.VariantType('(v)'), Gio.DBusCallFlags.NONE, 5000, None
        ).unpack()[0]
        
        # Get power-on time
        power_on_hours = connection.call_sync(
            'org.freedesktop.UDisks2', drive_path, 'org.freedesktop.DBus.Properties', 'Get',
            GLib.Variant('(ss)', (interface, 'SmartPowerOnHours')),
            GLib.VariantType('(v)'), Gio.DBusCallFlags.NONE, 5000, None
        ).unpack()[0]
        
        # Get detailed attributes
        attrs_dict = connection.call_sync(
            'org.freedesktop.UDisks2', drive_path, interface, 'SmartGetAttributes',
            GLib.Variant('(a{sv})', ({},)),
            GLib.VariantType('(a{sv})'), Gio.DBusCallFlags.NONE, 10000, None
        ).unpack()[0]
        
        # rename attributes
        attr_names = {
            'avail_spare': 'Available Spare',
            'spare_thresh': 'Available Spare Threshold',
            'percent_used': 'Percentage Used',
            'total_data_read': 'Total Data Read',
            'total_data_written': 'Total Data Written',
            'ctrl_busy_time': 'Controller Busy Time',
            'power_cycles': 'Power Cycles',
            'unsafe_shutdowns': 'Unsafe Shutdowns',
            'media_errors': 'Media Errors',
            'num_err_log_entries': 'Error Log Entries',
        }
        
        nvme_attrs = []
        for key, value in attrs_dict.items():
            nvme_attrs.append({
                'id': None, 
                'name': attr_names.get(key, key.replace('_', ' ').title()),
                'value': None,
                'worst': None,
                'thresh': None,
                'raw': {'value': value},
                'when_failed': ''
            })
        
        # Determine status
        status = 'healthy'
        if critical_warnings:
            status = 'failing' if any('spare' in w.lower() or 'reliability' in w.lower() for w in critical_warnings) else 'warning'
        
        data = {
            'temperature': {'current': int(temp_kelvin - 273.15)},
            'power_on_time': {'hours': power_on_hours},
            'smart_status': {'passed': not critical_warnings},
            'ata_smart_attributes': {'table': nvme_attrs},
            'is_nvme': True,
            'power_cycle_count': attrs_dict.get('power_cycles'),
            'unsafe_shutdowns': attrs_dict.get('unsafe_shutdowns'),
            'data_units_read': attrs_dict.get('total_data_read'),
            'data_units_written': attrs_dict.get('total_data_written'),
            'media_errors': attrs_dict.get('media_errors')
        }
        
        logger.info(f"Got SMART for {device_path} via NVMe: {int(temp_kelvin - 273.15)}°C, {power_on_hours}h, {len(nvme_attrs)} attrs, status={status}")
        return status, data
        
    except Exception as e:
        logger.warning(f"Could not get SMART via NVMe for {device_path}: {e}")
        return 'unavailable', {}