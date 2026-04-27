# recovery_dialog.py
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

from gi.repository import Gtk, Adw
import logging

@Gtk.Template(resource_path='/datarecovery/gtk/recovery_dialog.ui')
class RecoveryProgressDialog(Adw.AlertDialog):
    __gtype_name__ = 'RecoveryProgressDialog'
    
    status_label = Gtk.Template.Child()
    progress_bar = Gtk.Template.Child()
    steps_label = Gtk.Template.Child()
    
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.logger = logging.getLogger('datarecovery')
        self.recovery_complete = False
        self.cancelling = False 
        self.steps = []
        self.cancel_callback = None
        
        # Override the close-response to prevent auto-closing during recovery
        self.set_close_response("") 
        self.connect("response", self._on_response)
        
    def show(self):
        self.present(self.parent_window)
        self.recovery_complete = False
        self.cancelling = False
        self.cancel_callback = None  # Reset cancel callback
        self.logger.info("Recovery progress dialog shown")
    
    def setup_steps(self, steps):
        self.steps = [(step_id, desc, 'pending') for step_id, desc in steps]
        self._update_steps_display()
    
    def update_step_status(self, step_id, status):
        for i, (sid, desc, _) in enumerate(self.steps):
            if sid == step_id:
                self.steps[i] = (sid, desc, status)
                break
        self._update_steps_display()
    
    def _update_steps_display(self):
        def _update():
            lines = []
            for step_id, description, status in self.steps:
                if status == 'complete':
                    icon = '✓'
                    color = '#26a269'  # success green
                elif status == 'active':
                    icon = '◉'
                    color = '#1c71d8'  # accent blue
                elif status == 'error':
                    icon = '✗'
                    color = '#c01c28'  # error red
                else:  # pending
                    icon = '○'
                    color = '#9a9996'  # dim gray
                
                lines.append(f'<span foreground="{color}">{icon}</span>  {description}')
            
            self.steps_label.set_markup('\n'.join(lines))

        _update()
    
    def update_status(self, status_text):
        if self.status_label:
            self.status_label.set_markup(f"<b>{status_text}</b>")
    
    def update_progress(self, fraction=None):
        if fraction is not None and self.progress_bar:
            self.progress_bar.set_fraction(fraction)
    
    def mark_complete(self):
        self.recovery_complete = True
        self._change_button_to_close()
    
    def _change_button_to_close(self):
        self.set_response_label("cancel", "Close")
        self.set_response_appearance("cancel", Adw.ResponseAppearance.DEFAULT)
    
    def _on_response(self, dialog, response):
        if response == "cancel":
            if self.recovery_complete:
                self.logger.info("User closed recovery dialog after completion")
                self.close()
            elif not self.cancelling:
                self.logger.warning("User requested to cancel recovery")
                self.cancelling = True
                if self.cancel_callback:
                    try:
                        self.cancel_callback()
                    except Exception as e:
                        self.logger.error(f"Error during cancellation: {e}")
                else:
                    self.logger.warning("No cancel callback registered")
                    self.close()
            else:
                self.logger.info("Cancellation already in progress")
