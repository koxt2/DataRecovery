# settings.py
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

def apply_no_selection_settings(window):
    pass

def apply_device_selection_settings(window):
    window.save_image_switch.set_sensitive(True)

def apply_image_file_settings(window):
    window.save_image_switch.set_sensitive(False)
    window.save_image_switch.set_active(False)

def get_settings(window):
    settings = {
        'save_image': window.save_image_switch.get_active(),
        'save_logs': window.log_switch.get_active(),
        'keep_corrupted': window.corrupted_switch.get_active(),
        'remove_duplicates': window.dupes_switch.get_active()
    }
    
    # Get file type filter command if dialog exists
    if window.file_types_dialog is not None:
        settings['fileopt_command'] = window.file_types_dialog.get_photorec_fileopt_commands()
    else:
        # Default to all file types enabled
        settings['fileopt_command'] = 'fileopt,everything,enable'
    
    return settings
