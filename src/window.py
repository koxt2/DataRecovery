# window.py
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
from gi.repository import Adw, Gtk, Gio, GLib

from .about import about_dialog
from .device_dropdown import DeviceDropdown, SELECTION_NO_DEVICE, SELECTION_IMAGE_FILE
from .device_columnview import DeviceColumnView
from .block_devices import DeviceMonitor
from .mounted_check import MountedPartitionChecker
from .recovery_dialog import RecoveryProgressDialog
from .recovery_workflow import RecoveryWorkflow
from .file_types_dialog import FileTypesDialog
from . import settings

@Gtk.Template(resource_path='/datarecovery/gtk/window.ui')
class DatarecoveryWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'DatarecoveryWindow'
    
    mounted_factory                 = Gtk.Template.Child()
    device_path_factory             = Gtk.Template.Child()
    size_factory                    = Gtk.Template.Child()
    filesystem_factory              = Gtk.Template.Child()
    label_factory                   = Gtk.Template.Child()
    type_factory                    = Gtk.Template.Child()
    
    select_device_dropdown          = Gtk.Template.Child()
    device_liststore                = Gtk.Template.Child()
    
    columnview_liststore            = Gtk.Template.Child()
    columnview_model                = Gtk.Template.Child()
    
    save_image_switch               = Gtk.Template.Child()
    log_switch                      = Gtk.Template.Child()
    corrupted_switch                = Gtk.Template.Child()
    dupes_switch                    = Gtk.Template.Child()
    file_types_row                  = Gtk.Template.Child()
    
    choose_destination_actionrow    = Gtk.Template.Child()
    
    search_button                   = Gtk.Template.Child()  
    output_label                    = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.logger = logging.getLogger('datarecovery')
        self.working_dir = None
        
        self.device_dropdown = None
        self.device_monitor = None
        self.device_columnview = None
        self.mount_checker = None
        self.recovery_dialog = None
        self.file_types_dialog = None
        
        self.create_action('about', self.on_about_action)
    
    def initialize(self, working_dir):
        self.working_dir = working_dir
        
        self.device_dropdown = DeviceDropdown(self)
        self.device_monitor = DeviceMonitor(self.device_dropdown)
        self.device_columnview = DeviceColumnView(self, self.device_dropdown)
        self.mount_checker = MountedPartitionChecker(self, self.device_dropdown)
        self.recovery_dialog = RecoveryProgressDialog(self)
        
        self.select_device_dropdown.connect("notify::selected", self._on_device_selected)
        self.choose_destination_actionrow.connect("activated", lambda row: self._choose_destination())
        self.search_button.connect("clicked", lambda button: self._on_search())
        self.file_types_row.connect("activated", self.on_file_types_row_clicked)
        
        self.search_button.set_sensitive(False)
    
    def _update_search_button_sensitivity(self):
        """Enable search button only if both device and destination are set"""
        has_device = hasattr(self, 'device_path') and self.device_path is not None
        has_destination = hasattr(self, 'destination_path') and self.destination_path is not None
        
        is_ready = has_device and has_destination
        self.search_button.set_sensitive(is_ready)
        
        if is_ready:
            self.output_label.set_label("Ready to start recovery")
        else:
            self.output_label.set_label("Choose a device and destination")
    
    def _on_device_selected(self, widget, param):
        selected = self.select_device_dropdown.get_selected()
        
        if selected == SELECTION_NO_DEVICE:
            self.columnview_liststore.remove_all()

            if not self.device_dropdown.is_refreshing:
                settings.apply_no_selection_settings(self)
            self.device_path = None
            
        elif selected == SELECTION_IMAGE_FILE:
            self._on_image_file_selection()
            
        else:
            # Check if it's a physical device or an existing image file
            device = self.device_dropdown.get_device_from_selection(selected)
            
            if device:
                if not self.device_dropdown.is_refreshing:
                    settings.apply_device_selection_settings(self)
                self.device_columnview._populate_columnview(selected)
            else:
                # It's an existing image file
                selected_item = self.device_liststore.get_item(selected)
                if selected_item:
                    selected_text = selected_item.get_string()
                    if not self.device_dropdown.is_refreshing:
                        settings.apply_image_file_settings(self)
                    self.device_columnview.update_columnview_for_image(selected_text)
        
        self._update_search_button_sensitivity()
    
    def _on_image_file_selection(self):
        dialog = Gtk.FileDialog.new()
        dialog.set_modal(True)

        def on_file_selected(dialog, result, user_data):
            try:
                file = dialog.open_finish(result)
                if file:
                    image_path = file.get_path()
                    self.device_dropdown.add_image_to_selector(image_path)
                    self.device_columnview.update_columnview_for_image(image_path)
                    self._update_search_button_sensitivity()
                else:
                    self.select_device_dropdown.set_selected(SELECTION_NO_DEVICE)
            except Exception as e:
                self.select_device_dropdown.set_selected(SELECTION_NO_DEVICE)

        dialog.open(self, None, on_file_selected, None)
    
    def _choose_destination(self):
        dialog = Gtk.FileDialog.new()
        dialog.set_modal(True)

        def on_response(dialog, result, user_data):
            try:
                folder = dialog.select_folder_finish(result)
                if folder:
                    self.destination_path = folder.get_path()
                    self.choose_destination_actionrow.set_title(self.destination_path)
                    self._update_search_button_sensitivity()
            except Exception as e:
                self.logger.error(f"Dialog error: {e}")

        dialog.select_folder(self, None, on_response, None)
    
    def _on_search(self):
        user_settings = settings.get_settings(self)
        device_path = self.device_path
        
        def proceed_with_recovery():
            workflow = RecoveryWorkflow(self, self.working_dir, self.recovery_dialog)
            workflow.start_recovery(device_path, user_settings)
        
        self.mount_checker.check_and_handle_mounted_partitions(
            device_path, 
            proceed_with_recovery
        )
    
    def create_action(self, name, callback):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
    
    def on_about_action(self, *args):
        about_dialog.present(self) 
    
    def on_file_types_row_clicked(self, row):
        if self.file_types_dialog is None:
            self.file_types_dialog = FileTypesDialog(parent_window=self)
        self.file_types_dialog.present(self)
