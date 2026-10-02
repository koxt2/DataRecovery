# Copyright 2025 Richard Potts
# SPDX-License-Identifier: GPL-2.0-or-later

import os
import shutil

import gi

gi.require_version("Adw", "1")
from gi.repository import Adw, GLib

from .config import REQUIRED_TOOLS, WORKING_DIR_NAME
from .log import setup_datarecovery_logging


class Initializer:
    def __init__(self, window=None):
        self.window = window
        self.working_dir = self.setup_working_dir()
        self.logger = self.setup_logger(self.working_dir)

        # Only continue if all tools are available
        self.tools_available = self.run_tool_check()
        if self.tools_available:
            self.logger.info("Initialisation complete - starting application")
        else:
            self.logger.warning("Initialisation failed due to missing tools")

    def setup_working_dir(self):
        user_data_dir = GLib.get_user_data_dir()
        working_dir = os.path.join(user_data_dir, "datarecovery", WORKING_DIR_NAME)

        # Remove and recreate working directory to ensure it's empty
        if os.path.exists(working_dir):
            shutil.rmtree(working_dir, ignore_errors=True)
        os.makedirs(working_dir, exist_ok=True)

        return working_dir

    def setup_logger(self, working_dir):
        logger = setup_datarecovery_logging(working_dir)
        logger.info(f"Working directory: {working_dir}")
        return logger

    def run_tool_check(self):
        missing = [t for t in REQUIRED_TOOLS if not shutil.which(t)]
        if missing:
            self.logger.critical(f"Missing tools dialog shown: {missing}")
            dialog = Adw.AlertDialog.new("Missing dependencies", None)
            body = "The following required tools are not available on your system:\n\n"
            body += "\n".join([f"\u2022 {m}" for m in missing])
            dialog.set_body(body)
            dialog.add_response("quit", "Quit")
            dialog.set_close_response("quit")
            dialog.present(self.window)

            def on_response(dialog_obj, response):
                if response == "quit":
                    if self.window:
                        app = self.window.get_application()
                        if app:
                            app.quit()

            dialog.connect("response", on_response)
            return False
        else:
            self.logger.info("All required tools are available")
            return True
