# smart_dialog.py
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

from gi.repository import Adw, Gtk, GObject
from . import smart_data
from .smart_dialog_columnview import SmartDialogColumnView
import logging

logger = logging.getLogger('datarecovery')

@Gtk.Template(resource_path='/datarecovery/gtk/smart_dialog.ui')
class SmartDialog(Adw.Dialog):
    __gtype_name__ = 'SmartDialog'
    
    status_value = Gtk.Template.Child()
    metrics_group = Gtk.Template.Child()
    attributes_label = Gtk.Template.Child()
    attributes_liststore = Gtk.Template.Child()
    id_factory = Gtk.Template.Child()
    name_factory = Gtk.Template.Child()
    value_factory = Gtk.Template.Child()
    worst_factory = Gtk.Template.Child()
    thresh_factory = Gtk.Template.Child()
    raw_factory = Gtk.Template.Child()
    
    def __init__(self, parent, device_path):
        super().__init__()
        self.device_path = device_path
        self.set_title(f"SMART Data: {device_path}")
        
        self.smart_dialog_columnview = SmartDialogColumnView(self)
        
        status, data = smart_data.get_smart_status(device_path)
        
        if data.get('is_nvme', False):  # is_nvme == True
            self._populate_nvme(status, data)
        else:  # is_nvme == False (ATA device)
            self._populate_ata(status, data)
    
    def _populate_nvme(self, status, data):
        self._set_status_label(status)
        
        self._add_temperature(data)
        self._add_power_on_time(data)
        
        # NVMe-specific metrics
        data_units_read = data.get('data_units_read')
        data_units_written = data.get('data_units_written')
        if data_units_read is not None or data_units_written is not None:
            read_str = f"{data_units_read / (1024**3):,.1f} GB" if data_units_read else "N/A"
            write_str = f"{data_units_written / (1024**3):,.1f} GB" if data_units_written else "N/A"
            self._add_row(self.metrics_group, "Data Read / Written", f"{read_str} / {write_str}")
        
        media_errors = data.get('media_errors')
        if media_errors is not None and media_errors > 0:
            self._add_row(self.metrics_group, "Media Errors", f"{media_errors:,} ⚠")
        
        attributes = self._extract_attributes(data)
        self.smart_dialog_columnview.populate_attributes(attributes)
    
    def _populate_ata(self, status, data):
        self._set_status_label(status)
        
        self._add_temperature(data)
        self._add_power_on_time(data)
        
        attributes = self._extract_attributes(data)
        
        reallocated_sectors = None
        pending_sectors = None
        offline_uncorrectable = None
        
        for attr in attributes:
            if attr['id'] == 5:
                reallocated_sectors = attr['raw']
            elif attr['id'] == 197:
                pending_sectors = attr['raw']
            elif attr['id'] == 198:
                offline_uncorrectable = attr['raw']
        
        if reallocated_sectors is not None:
            val = f"{reallocated_sectors}{' ⚠' if reallocated_sectors > 0 else ''}"
            self._add_row(self.metrics_group, "Reallocated Sectors", val)
        
        if pending_sectors is not None:
            val = f"{pending_sectors}{' ⚠' if pending_sectors > 0 else ''}"
            self._add_row(self.metrics_group, "Pending Sectors", val)
        
        if offline_uncorrectable is not None:
            val = f"{offline_uncorrectable}{' ⚠' if offline_uncorrectable > 0 else ''}"
            self._add_row(self.metrics_group, "Offline Uncorrectable", val)
        
        error_log = data.get('ata_smart_error_log', {})
        if error_log and error_log.get('count', 0) > 0:
            self._add_row(self.metrics_group, "Error Log Entries", f"{error_log['count']} ⚠")
        
        self.smart_dialog_columnview.populate_attributes(attributes)
    
    def _set_status_label(self, status):
        self.status_value.set_label(status.upper())
        if status == 'healthy':
            self.status_value.add_css_class("success")
        elif status == 'warning':
            self.status_value.add_css_class("warning")
        elif status == 'failing':
            self.status_value.add_css_class("error")
    
    def _add_temperature(self, data):
        temp = data.get('temperature', {}).get('current')
        if temp is not None:
            self._add_row(self.metrics_group, "Temperature", f"{temp}°C")
    
    def _add_power_on_time(self, data):
        hours = data.get('power_on_time', {}).get('hours')
        if hours is not None:
            years = hours // 8760
            months = (hours % 8760) // 730
            days = ((hours % 8760) % 730) // 24
            
            if years > 0:
                time_str = f"{hours:,} hours ({years}y {months}m)"
            elif months > 0:
                time_str = f"{hours:,} hours ({months}m {days}d)"
            else:
                time_str = f"{hours:,} hours ({days}d)"
            
            self._add_row(self.metrics_group, "Power-On Time", time_str)
    
    def _extract_attributes(self, data):
        attributes = []
        for attr in data.get('ata_smart_attributes', {}).get('table', []):
            attributes.append({
                'id': attr.get('id'),
                'name': attr.get('name', ''),
                'value': attr.get('value', 0),
                'worst': attr.get('worst', 0),
                'thresh': attr.get('thresh', 0),
                'raw': attr.get('raw', {}).get('value', 0),
                'failed': attr.get('when_failed', '') != ''
            })
        return attributes
    
    def _add_row(self, group, title, value):
        row = Adw.ActionRow()
        row.set_title(title)
        value_label = Gtk.Label(label=value)
        value_label.add_css_class("dim-label")
        value_label.set_halign(Gtk.Align.END)
        row.add_suffix(value_label)
        group.add(row)
