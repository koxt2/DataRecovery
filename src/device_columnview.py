# device_columnview.py
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
from gi.repository import GObject, Gtk

from .partition_guids import PARTITION_TYPE_GUIDS
from . import settings
from . import smart_data
from .smart_dialog import SmartDialog
from .utils import format_size

class PartitionRow(GObject.Object):
    __gtype_name__ = 'PartitionRow'

    def __init__(self, mounted=False, path='', size='', filesystem='', label='', part_type='', mount_path=None, smart_status='unavailable', is_whole_device=False):
        super().__init__()
        self._mounted = mounted
        self._path = path
        self._size = size
        self._filesystem = filesystem
        self._label = label
        self._type = part_type
        self._mount_path = mount_path
        self._smart_status = smart_status
        self._is_whole_device = is_whole_device

    @GObject.Property(type=bool, default=False)
    def mounted(self):
        return self._mounted

    @GObject.Property(type=str)
    def path(self):
        return self._path or ''

    @GObject.Property(type=str)
    def size(self):
        return self._size or ''

    @GObject.Property(type=str)
    def filesystem(self):
        return self._filesystem or ''

    @GObject.Property(type=str)
    def label(self):
        return self._label or ''

    @GObject.Property(type=str)
    def part_type(self):
        return self._type or ''

    @GObject.Property(type=str)
    def mount_path(self):
        return self._mount_path or ''
    
    @GObject.Property(type=str)
    def smart_status(self):
        return self._smart_status or 'unavailable'
    
    @GObject.Property(type=bool, default=False)
    def is_whole_device(self):
        return self._is_whole_device

class DeviceColumnView:
    def __init__(self, window, device_dropdown):
        self.window = window
        self.device_dropdown = device_dropdown
        self.setup_factories()

        self.window.columnview_model.connect('notify::selected', self.on_row_selected)

    def setup_factories(self):
        self.window.mounted_factory.connect("setup", self._mounted_factory_setup)
        self.window.mounted_factory.connect("bind", self._mounted_factory_bind('mounted'))
        self.window.device_path_factory.connect("setup", self._label_factory_setup)
        self.window.device_path_factory.connect("bind", self._label_factory_bind('path'))
        self.window.size_factory.connect("setup", self._label_factory_setup)
        self.window.size_factory.connect("bind", self._label_factory_bind('size'))
        self.window.filesystem_factory.connect("setup", self._label_factory_setup)
        self.window.filesystem_factory.connect("bind", self._label_factory_bind('filesystem'))
        self.window.label_factory.connect("setup", self._label_factory_setup)
        self.window.label_factory.connect("bind", self._label_factory_bind('label'))
        self.window.type_factory.connect("setup", self._label_factory_setup)
        self.window.type_factory.connect("bind", self._label_factory_bind('part_type'))
        self.window.health_factory.connect("setup", self._health_factory_setup)
        self.window.health_factory.connect("bind", self._health_factory_bind)
    
    def _label_factory_setup(self, factory, item):
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        item.set_child(label)

    def _label_factory_bind(self, prop):
        def bind_func(factory, item):
            label = item.get_child()
            row = item.get_item()
            value = getattr(row, prop, '') or ''  # Convert None to empty string
            label.set_label(str(value))
            self._set_mount_tooltip(label, row)
        return bind_func
    
    def _mounted_factory_setup(self, factory, item):
        check = Gtk.CheckButton()
        check.set_sensitive(False)
        check.set_halign(Gtk.Align.CENTER)
        item.set_child(check)

    def _mounted_factory_bind(self, prop):
        def bind_func(factory, item):
            check = item.get_child()
            row = item.get_item()
            # The mounted property is expected to be a bool
            check.set_active(bool(getattr(row, prop, False)))
            self._set_mount_tooltip(check, row)
        return bind_func
    
    def _health_factory_setup(self, factory, item):
        button = Gtk.Button()
        button.set_has_frame(False)
        button.add_css_class("flat")
        
        icon = Gtk.Image()
        icon.set_halign(Gtk.Align.CENTER)
        
        button.set_child(icon)
        item.set_child(button)
    
    def _health_factory_bind(self, factory, item):
        button = item.get_child()
        icon = button.get_child()
        
        row = item.get_item()
        status = row.smart_status
        is_device = row.is_whole_device
        
        # Only show SMART data for whole devices, not partitions
        if not is_device:
            icon.set_from_icon_name("")
            button.set_sensitive(False)
            button.set_tooltip_text(None)
            return
        
        if status == 'healthy':
            icon.set_from_icon_name("checkbox-checked-symbolic")
            button.set_tooltip_text("Click for detailed SMART data")
        elif status == 'warning':
            icon.set_from_icon_name("dialog-warning-symbolic")
            button.set_tooltip_text("Click for detailed SMART data")
        elif status == 'failing':
            icon.set_from_icon_name("dialog-error-symbolic")
            button.set_tooltip_text("Click for detailed SMART data")
        else:  # unavailable
            icon.set_from_icon_name("dialog-question-symbolic")
            button.set_tooltip_text("SMART data not available")
        
        # Disconnect the button so the same handler is not connected multiple times
        if hasattr(button, '_health_handler_id'):
            button.disconnect(button._health_handler_id)
        
        handler_id = button.connect('clicked', self._on_health_clicked, row.path)
        button._health_handler_id = handler_id
        
        button.set_sensitive(status != 'unavailable')
    
    def _on_health_clicked(self, button, device_path):
        dialog = SmartDialog(self.window, device_path)
        dialog.present(self.window)
   
    def _set_mount_tooltip(self, widget, row):
        if getattr(row, 'mounted', False):
            mount_path = getattr(row, 'mount_path', None)
            if mount_path:
                widget.set_tooltip_text(f"Mounted at: {mount_path}")
            else:
                widget.set_tooltip_text("Mounted")
        else:
            widget.set_tooltip_text(None)
    
    def _populate_columnview(self, selection_idx):
        self.window.columnview_liststore.remove_all()
        
        device = self.device_dropdown.get_device_from_selection(selection_idx)
        
        if not device:
            return
        
        # Find partitions for this device
        matching_parts = [
            p for p in self.device_dropdown.partitions
            if p['path'].startswith(device['path']) and p['path'] != device['path']
        ]
        
        # Get SMART status for the device
        smart_status, _ = smart_data.get_smart_status(device['path'])
        
        # Always show the whole device as a row
        size_str = format_size(device.get('size', 0))
        part_type_name = 'WHOLE DEVICE'
        row = PartitionRow(
            mounted=device.get('mounted', False),
            path=device['path'],
            size=size_str,
            filesystem=device.get('id_type', ''),
            label=device.get('label', ''),
            part_type=part_type_name,
            mount_path=device.get('mount_path'),
            smart_status=smart_status,
            is_whole_device=True
        )
        self.window.columnview_liststore.append(row)
        
        # Then show all partitions (if any)
        for p in matching_parts:
            size_str = format_size(p.get('size', 0))
            part_type_guid = p.get('parttype', '')
            part_type_name = PARTITION_TYPE_GUIDS.get(part_type_guid.lower(), part_type_guid) if part_type_guid else ''
            row = PartitionRow(
                mounted=p.get('mounted', False),
                path=p.get('path', ''),
                size=size_str,
                filesystem=p.get('id_type', ''),
                label=p.get('label', ''),
                part_type=part_type_name,
                mount_path=p.get('mount_path')
            )
            self.window.columnview_liststore.append(row)
        
        settings.apply_device_selection_settings(self.window)

    def update_columnview_for_image(self, image_path):
        self.window.columnview_liststore.remove_all()
        
        try:
            size_bytes = os.path.getsize(image_path) if os.path.exists(image_path) else 0
            size_str = format_size(size_bytes)
        except (OSError, IOError):
            size_str = "Unknown"
        
        row = PartitionRow(
            mounted=False,
            path=image_path,
            size=size_str,
            filesystem='',
            label=os.path.basename(image_path),
            part_type='IMAGE FILE',
            mount_path=None
        )
        self.window.columnview_liststore.append(row)
        
        settings.apply_image_file_settings(self.window)
        return True
    
    def on_row_selected(self, selection, param):
        selected_index = self.window.columnview_model.get_selected()
        if selected_index != -1:
            item = self.window.columnview_liststore.get_item(selected_index)
            if item is not None:
                self.window.device_path = item.path
                self.window.filesystem = item.filesystem