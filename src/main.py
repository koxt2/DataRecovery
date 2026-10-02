# Copyright 2025 Richard Potts
# SPDX-License-Identifier: GPL-2.0-or-later

import sys

import gi

gi.require_version("Adw", "1")
from gi.repository import Adw, Gio

from .initializer import Initializer
from .window import DatarecoveryWindow


class DatarecoveryApplication(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.github.koxt2.datarecovery",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = DatarecoveryWindow(application=self)
            win.present()

            initializer = Initializer(window=win)
            if initializer.tools_available:
                win.setup_window(working_dir=initializer.working_dir)
        else:
            win.present()

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main():
    app = DatarecoveryApplication()
    return app.run(sys.argv)
