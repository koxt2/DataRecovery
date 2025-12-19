# custom_signature_dialog.py
#
# Copyright 2025 koxt2
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging
from pathlib import Path
from gi.repository import Gtk, Adw, GLib


@Gtk.Template(resource_path='/datarecovery/gtk/custom_signature_dialog.ui')
class CustomSignatureDialog(Adw.Dialog):
    __gtype_name__ = 'CustomSignatureDialog'

    # UI Elements
    file_chooser_button = Gtk.Template.Child()
    selected_file_row = Gtk.Template.Child()
    selected_file_label = Gtk.Template.Child()
    extension_entry = Gtk.Template.Child()
    byte_length_spin = Gtk.Template.Child()
    signature_preview_row = Gtk.Template.Child()
    hex_signature_row = Gtk.Template.Child()
    ascii_preview_row_display = Gtk.Template.Child()
    add_signature_button = Gtk.Template.Child()
    signatures_list = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.logger = logging.getLogger('datarecovery')
        self.selected_file_path = None
        self.current_signature = None
        
        self.photorec_sig_file = Path.home() / '.photorec.sig'
        self.logger.info(f"Custom signature file: {self.photorec_sig_file}")
        
        self.file_chooser_button.connect('clicked', self.on_choose_file)
        self.byte_length_spin.connect('value-changed', self.on_byte_length_changed)
        self.add_signature_button.connect('clicked', self.on_add_signature)
        
        self.load_existing_signatures()

    def on_choose_file(self, button):
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Choose Sample File")
        
        file_dialog.open(self.get_root(), None, self.on_file_selected)

    def on_file_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                self.selected_file_path = file.get_path()
                filename = Path(self.selected_file_path).name
                
                self.selected_file_label.set_label(filename)
                self.selected_file_row.set_visible(True)
                
                extension = Path(filename).suffix.lstrip('.')
                if extension:
                    self.extension_entry.set_text(extension)
                
                self.extract_signature()
                
        except GLib.Error as e:
            print(f"Error selecting file: {e}")

    def extract_signature(self):
        if not self.selected_file_path:
            return
        
        num_bytes = int(self.byte_length_spin.get_value())
        
        try:
            with open(self.selected_file_path, 'rb') as f:
                header = f.read(num_bytes)
            
            if not header:
                return
            
            # Convert to hex (without 0x prefix for PhotoRec format)
            hex_sig = header.hex()
            
            # Create ASCII preview (show printable chars, dots for non-printable)
            ascii_preview = ''.join(
                chr(b) if 32 <= b < 127 else '.' 
                for b in header
            )
            
            self.current_signature = {
                'hex': hex_sig,
                'preview': ascii_preview,
                'bytes': header
            }
            
            self.hex_signature_row.set_subtitle(f"0x{hex_sig}")
            self.ascii_preview_row_display.set_subtitle(ascii_preview)
            self.signature_preview_row.set_visible(True)
            
            if self.extension_entry.get_text().strip():
                self.add_signature_button.set_sensitive(True)
                
        except Exception as e:
            print(f"Error extracting signature: {e}")

    def on_byte_length_changed(self, spin):
        if self.selected_file_path:
            self.extract_signature()

    def on_add_signature(self, button):
        """Add the signature to photorec.sig file"""
        extension = self.extension_entry.get_text().strip()
        
        if not extension or not self.current_signature:
            self.logger.warning("Cannot add signature: missing extension or signature")
            return
        
        signature_line = f"{extension} 0 0x{self.current_signature['hex']}\n"
        
        try:
            # Append to photorec.sig file
            with open(self.photorec_sig_file, 'a') as f:
                f.write(signature_line)
            
            self.logger.info(f"Added custom signature: {extension} with hex {self.current_signature['hex']}")
            
            self.reset_form()
            
            self.load_existing_signatures()
            
        except Exception as e:
            self.logger.error(f"Error saving signature: {e}")
            print(f"Error saving signature: {e}")

    def load_existing_signatures(self):
        # Clear existing list
        while True:
            row = self.signatures_list.get_row_at_index(0)
            if row:
                self.signatures_list.remove(row)
            else:
                break
        
        if not self.photorec_sig_file.exists():
            row = Adw.ActionRow()
            row.set_title("No custom signatures yet")
            row.set_subtitle("Add a signature by selecting a sample file above")
            self.signatures_list.append(row)
            return
        
        try:
            with open(self.photorec_sig_file, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                row = Adw.ActionRow()
                row.set_title("No custom signatures yet")
                self.signatures_list.append(row)
                return
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse: extension offset hex_signature
                parts = line.split(None, 2)
                if len(parts) >= 3:
                    extension, offset, hex_sig = parts
                    
                    row = Adw.ActionRow()
                    row.set_title(f".{extension}")
                    row.set_subtitle(f"Signature: {hex_sig[:32]}..." if len(hex_sig) > 32 else f"Signature: {hex_sig}")
                    
                    delete_btn = Gtk.Button()
                    delete_btn.set_icon_name("user-trash-symbolic")
                    delete_btn.set_valign(Gtk.Align.CENTER)
                    delete_btn.add_css_class("flat")
                    delete_btn.add_css_class("circular")
                    delete_btn.connect('clicked', self.on_delete_signature, line)
                    row.add_suffix(delete_btn)
                    
                    self.signatures_list.append(row)
                    
        except Exception as e:
            self.logger.error(f"Error loading signatures: {e}")
            print(f"Error loading signatures: {e}")

    def on_delete_signature(self, button, signature_line):
        try:
            with open(self.photorec_sig_file, 'r') as f:
                lines = f.readlines()
            
            # Remove the signature line
            lines = [line for line in lines if line.strip() != signature_line.strip()]
            
            # Write back
            with open(self.photorec_sig_file, 'w') as f:
                f.writelines(lines)
            
            self.logger.info(f"Deleted custom signature: {signature_line.strip()}")
            
            self.load_existing_signatures()
            
        except Exception as e:
            self.logger.error(f"Error deleting signature: {e}")
            print(f"Error deleting signature: {e}")

    def reset_form(self):
        """Reset the form to initial state"""
        self.selected_file_path = None
        self.current_signature = None
        self.selected_file_row.set_visible(False)
        self.selected_file_label.set_label("")
        self.extension_entry.set_text("")
        self.byte_length_spin.set_value(16)
        self.signature_preview_row.set_visible(False)
        self.add_signature_button.set_sensitive(False)
