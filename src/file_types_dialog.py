# file_types_dialog.py
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

from gi.repository import Adw, Gtk
from .config import FILE_TYPES

@Gtk.Template(resource_path='/datarecovery/gtk/file_types.ui')
class FileTypesDialog(Adw.Dialog):
    __gtype_name__ = 'FileTypesDialog'
    
    container_box = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    select_all_button = Gtk.Template.Child()
    unselect_all_button = Gtk.Template.Child()
    
    def __init__(self, parent_window, **kwargs):
        super().__init__(**kwargs)
        self.category_boxes = {}
        self.file_type_rows = {}
        self.category_switches = {}
        self.populate_file_types()
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.select_all_button.connect("clicked", self.on_select_all)
        self.unselect_all_button.connect("clicked", self.on_unselect_all)
    
    def populate_file_types(self):
        for category, file_types in FILE_TYPES.items():
            expander_row = Adw.ExpanderRow()
            expander_row.set_title(category)
            expander_row.set_expanded(False)
            
            category_switch = Gtk.Switch()
            category_switch.set_valign(Gtk.Align.CENTER)
            category_switch.set_active(True)
            expander_row.add_suffix(category_switch)
            
            listbox = Gtk.ListBox()
            listbox.set_css_classes(["boxed-list"])
            listbox.set_selection_mode(Gtk.SelectionMode.NONE)

            self.file_type_rows[category] = []

            for file_type in file_types:
                switch_row = Adw.SwitchRow()
                switch_row.set_title(file_type)
                switch_row.set_active(True)
                listbox.append(switch_row)
                self.file_type_rows[category].append((switch_row, file_type))

            category_switch.connect("state-set", self.on_category_switch_toggled, category)
            
            expander_row.add_row(listbox)
            self.container_box.add(expander_row)
            self.category_boxes[category] = expander_row
            self.category_switches[category] = category_switch
    
    def on_category_switch_toggled(self, switch, state, category):
        for switch_row, file_type in self.file_type_rows[category]:
            switch_row.set_active(state)
        return False
    
    def on_search_changed(self, entry):
        search_text = entry.get_text().lower()
        
        if not search_text:
            # Show all categories and rows
            for category_box in self.category_boxes.values():
                category_box.set_visible(True)
            for category_rows in self.file_type_rows.values():
                for switch_row, file_type in category_rows:
                    switch_row.set_visible(True)
        else:
            # Filter based on search text
            for category, category_box in self.category_boxes.items():
                has_visible_items = False
                
                # Check each file type in this category
                for switch_row, file_type in self.file_type_rows[category]:
                    matches = search_text in file_type.lower()
                    switch_row.set_visible(matches)
                    if matches:
                        has_visible_items = True
                
                # Show/hide the entire category based on whether it has visible items
                category_box.set_visible(has_visible_items)
    
    def on_select_all(self, button):
        for category_switch in self.category_switches.values():
            category_switch.set_active(True)
        for category_rows in self.file_type_rows.values():
            for switch_row, file_type in category_rows:
                switch_row.set_active(True)
    
    def on_unselect_all(self, button):
        for category_switch in self.category_switches.values():
            category_switch.set_active(False)
        for category_rows in self.file_type_rows.values():
            for switch_row, file_type in category_rows:
                switch_row.set_active(False)
    
    def get_selected_file_types(self):
        selected = []
        for category_rows in self.file_type_rows.values():
            for switch_row, file_type in category_rows:
                if switch_row.get_active():
                    selected.append(file_type)
        return selected
    
    def get_photorec_fileopt_commands(self):
        selected = self.get_selected_file_types()
        
        total_count = sum(len(rows) for rows in self.file_type_rows.values())
        selected_count = len(selected)
        
        if selected_count == 0:
            return "fileopt,everything,disable"
        elif selected_count == total_count:
            return "fileopt,everything,enable"
        elif selected_count > total_count / 2: ########## This needs testing ##########
            # More than half selected - use exclude mode (disable unselected)
            all_file_types = []
            for category_rows in self.file_type_rows.values():
                for switch_row, file_type in category_rows:
                    all_file_types.append(file_type)
            
            # Disable the ones that are NOT selected
            unselected = [ft for ft in all_file_types if ft not in selected]
            parts = ["fileopt", "everything", "enable"]
            for file_type in unselected:
                parts.extend([file_type, "disable"])
            return ",".join(parts)
        else:
            # Less than half selected - use include mode (enable only selected)
            parts = ["fileopt", "everything", "disable"]
            for file_type in selected:
                parts.extend([file_type, "enable"])
            return ",".join(parts)
