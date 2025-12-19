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
from pathlib import Path
import logging
from .file_types import FILE_TYPES, FILE_TYPE_GROUPS
from .custom_signature_dialog import CustomSignatureDialog

@Gtk.Template(resource_path='/datarecovery/gtk/file_types.ui')
class FileTypesDialog(Adw.Dialog):
    __gtype_name__ = 'FileTypesDialog'
    
    container_box = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    select_all_button = Gtk.Template.Child()
    unselect_all_button = Gtk.Template.Child()
    custom_signatures_button = Gtk.Template.Child()
    
    def __init__(self, parent_window, **kwargs):
        super().__init__(**kwargs)
        self.parent_window = parent_window
        self.category_boxes = {}
        self.file_type_rows = {}
        self.category_switches = {}
        self.group_boxes = {}  
        self.extension_to_family = {}  # Maps extension -> family key for photorec.cfg
        self.custom_signature_dialog = None
        self.photorec_sig_file = Path.home() / '.photorec.sig'
        self.logger = logging.getLogger('datarecovery')
        
        self.populate_file_types()
        self.reload_custom_signatures() 
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.select_all_button.connect("clicked", self.on_select_all)
        self.unselect_all_button.connect("clicked", self.on_unselect_all)
        self.custom_signatures_button.connect("clicked", self.on_custom_signatures_clicked)
    
    def populate_file_types(self):
        for group_name, categories in FILE_TYPE_GROUPS.items():
            group = Adw.PreferencesGroup()
            group.set_title(group_name)
            self.group_boxes[group_name] = group
            
            for category in categories:
                if category not in FILE_TYPES:
                    continue
                    
                families = FILE_TYPES[category]
                
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

                # Iterate through families and their extensions
                for family, extensions in families.items():
                    for extension in extensions:
                        # Map extension to its family for photorec.cfg
                        self.extension_to_family[extension] = family
                        
                        switch_row = Adw.SwitchRow()
                        switch_row.set_title(extension)
                        switch_row.set_active(True)
                        switch_row.connect("notify::active", self.on_file_type_switch_changed, category)
                        listbox.append(switch_row)
                        self.file_type_rows[category].append((switch_row, extension))

                category_switch.connect("state-set", self.on_category_switch_toggled, category)
                
                expander_row.add_row(listbox)
                group.add(expander_row)
                self.category_boxes[category] = expander_row
                self.category_switches[category] = category_switch
            
            # Add the group to the main container
            self.container_box.append(group)
    
    def on_category_switch_toggled(self, switch, state, category):
        """User toggled category switch - set all file types to match"""
        for row, _ in self.file_type_rows[category]:
            if hasattr(row, 'set_active'):
                row.set_active(state)
        return False
    
    def on_file_type_switch_changed(self, switch_row, param, category):
        """File type changed - update category indicator without triggering toggle"""
        any_active = any(
            row.get_active() for row, _ in self.file_type_rows[category] 
            if hasattr(row, 'get_active')
        )
        self.update_category_indicator(category, any_active)
    
    def update_category_indicator(self, category, active):
        """Update category switch without triggering the toggle handler"""
        switch = self.category_switches.get(category)
        if switch and switch.get_active() != active:
            switch.handler_block_by_func(self.on_category_switch_toggled)
            switch.set_active(active)
            switch.handler_unblock_by_func(self.on_category_switch_toggled)
    
    def on_search_changed(self, entry):
        search_text = entry.get_text().lower()
        
        if not search_text:
            # Show all groups, categories and rows
            for group_box in self.group_boxes.values():
                group_box.set_visible(True)
            for category_box in self.category_boxes.values():
                category_box.set_visible(True)
            for category_rows in self.file_type_rows.values():
                for switch_row, file_type in category_rows:
                    switch_row.set_visible(True)
        else:
            # Track which groups have visible categories
            group_has_visible = {group: False for group in self.group_boxes}
            
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
                
                # Track if this category's group has visible items
                if has_visible_items:
                    for group_name, categories in FILE_TYPE_GROUPS.items():
                        if category in categories:
                            group_has_visible[group_name] = True
                            break
            
            # Show/hide groups based on whether they have visible categories
            for group_name, group_box in self.group_boxes.items():
                group_box.set_visible(group_has_visible.get(group_name, False))
    
    def on_select_all(self, button):
        for category_switch in self.category_switches.values():
            category_switch.set_active(True)
        for category_rows in self.file_type_rows.values():
            for row, file_type in category_rows:
                if hasattr(row, 'set_active'):
                    row.set_active(True)
    
    def on_unselect_all(self, button):
        for category_switch in self.category_switches.values():
            category_switch.set_active(False)
        for category_rows in self.file_type_rows.values():
            for row, file_type in category_rows:
                if hasattr(row, 'set_active'):
                    row.set_active(False)
    
    def get_selected_file_types(self):
        selected = []
        for category, category_rows in self.file_type_rows.items():
            for row, extension in category_rows:
                # For rows with switches (SwitchRow), check individual switch
                if hasattr(row, 'get_active'):
                    if row.get_active():
                        selected.append(extension)
                # For rows without switches (Custom Signatures), check category switch
                elif category in self.category_switches:
                    if self.category_switches[category].get_active():
                        selected.append(extension)
        return selected
    
    def on_custom_signatures_clicked(self, button):
        if self.custom_signature_dialog is None:
            self.custom_signature_dialog = CustomSignatureDialog()
            self.custom_signature_dialog.connect("closed", self.on_custom_dialog_closed)
        self.custom_signature_dialog.present(self.parent_window)
    
    def on_custom_dialog_closed(self, dialog):
        self.reload_custom_signatures()
    
    def reload_custom_signatures(self):
        # Remove existing custom signatures category if it exists
        if "Custom Signatures" in self.category_boxes:
            old_row = self.category_boxes["Custom Signatures"]
            system_group = self.group_boxes.get("System &amp; Other")
            if system_group:
                system_group.remove(old_row)
            del self.category_boxes["Custom Signatures"]
            del self.file_type_rows["Custom Signatures"]
            if "Custom Signatures" in self.category_switches:
                del self.category_switches["Custom Signatures"]
        
        if not self.photorec_sig_file.exists():
            return
        
        # Read custom signatures
        try:
            with open(self.photorec_sig_file, 'r') as f:
                lines = f.readlines()
            
            custom_extensions = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse: extension offset hex_signature
                parts = line.split(None, 2)
                if len(parts) >= 3:
                    extension = parts[0]
                    custom_extensions.append(extension)
            
            if not custom_extensions:
                return
            
            # Create Custom Signatures category
            expander_row = Adw.ExpanderRow()
            expander_row.set_title("Custom Signatures")
            expander_row.set_expanded(False)
            
            category_switch = Gtk.Switch()
            category_switch.set_valign(Gtk.Align.CENTER)
            category_switch.set_active(True)
            expander_row.add_suffix(category_switch)
            
            listbox = Gtk.ListBox()
            listbox.set_css_classes(["boxed-list"])
            listbox.set_selection_mode(Gtk.SelectionMode.NONE)

            self.file_type_rows["Custom Signatures"] = []

            for extension in custom_extensions:
                action_row = Adw.ActionRow()
                action_row.set_title(extension)
                listbox.append(action_row)
                self.file_type_rows["Custom Signatures"].append((action_row, extension))

            category_switch.connect("state-set", self.on_category_switch_toggled, "Custom Signatures")
            
            expander_row.add_row(listbox)
            # Add to System & Other group
            system_group = self.group_boxes.get("System &amp; Other")
            if system_group:
                system_group.add(expander_row)
            self.category_boxes["Custom Signatures"] = expander_row
            self.category_switches["Custom Signatures"] = category_switch
            
        except Exception as e:
            print(f"Error loading custom signatures: {e}")
    
    def write_photorec_cfg(self):
        selected_extensions = self.get_selected_file_types()
        photorec_cfg_file = Path.home() / '.photorec.cfg'
        
        self.logger.info(f"Writing PhotoRec configuration file: {photorec_cfg_file}")
        self.logger.info(f"Selected extensions: {len(selected_extensions)} types")
        
        lines = []
        
        # Handle custom signatures - enable/disable based on category switch
        custom_enabled = False
        if "Custom Signatures" in self.category_switches:
            custom_enabled = self.category_switches["Custom Signatures"].get_active()
        lines.append(f"custom,{'enable' if custom_enabled else 'disable'}")
        self.logger.debug(f"Custom signatures: {'enabled' if custom_enabled else 'disabled'}")
        
        # Collect all families and determine if they should be enabled
        # A family is enabled if ANY of its extensions are selected
        family_enabled = {}
        for category, families in FILE_TYPES.items():
            for family, extensions in families.items():
                if family not in family_enabled:
                    family_enabled[family] = False
                if any(ext in selected_extensions for ext in extensions):
                    family_enabled[family] = True
        
        enabled_count = sum(1 for enabled in family_enabled.values() if enabled)
        self.logger.info(f"Enabling {enabled_count} file families out of {len(family_enabled)} total")
        self.logger.debug(f"Enabled families: {sorted([f for f, e in family_enabled.items() if e])}")
        
        # Write each family's enable/disable status
        for family, enabled in family_enabled.items():
            lines.append(f"{family},{'enable' if enabled else 'disable'}")
        
        # Write to config file
        try:
            with open(photorec_cfg_file, 'w') as f:
                f.write('\n'.join(lines) + '\n')
            self.logger.info(f"PhotoRec configuration written successfully: {len(lines)} entries")
        except Exception as e:
            self.logger.error(f"Error writing photorec.cfg: {e}")
