# main.py
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

import sys
import gi

gi.require_version('Adw', '1')
from gi.repository import Adw, Gio

from .window import DatarecoveryWindow
from .initialiser import Initialiser

class DatarecoveryApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.github.koxt2.datarecovery',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = DatarecoveryWindow(application=self)
        win.present()

        initialiser = Initialiser(window=win)
        
        if initialiser.tools_available:
            win.initialize(working_dir=initialiser.working_dir)

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

def main():
    app = DatarecoveryApplication()
    return app.run(sys.argv)