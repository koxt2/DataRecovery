# Copyright 2025 Richard Potts
# SPDX-License-Identifier: GPL-2.0-or-later

import logging
import os
import subprocess

from gi.repository import GLib

from .config import DUPLICATES_LOG


class DuplicateRemover:
    def __init__(self, recovery_dialog=None, working_dir=None):
        self.recovery_dialog = recovery_dialog
        self.working_dir = working_dir
        self.logger = logging.getLogger("datarecovery")
        self.current_process = None
        self.cancelled = False

    def remove_duplicates(self, recovery_dir):
        self.cancelled = False
        self.logger.info("=== Scanning For Duplicates ===")
        self.logger.info(f"Scanning for duplicates in: {recovery_dir}")

        if self.recovery_dialog:
            GLib.idle_add(self.recovery_dialog.update_status, "Removing duplicate files...")

        results_filename = DUPLICATES_LOG
        results_path = os.path.join(self.working_dir, results_filename)

        cmd = [
            "rdfind",
            "-deleteduplicates",
            "true",
            "-outputname",
            results_path,
            recovery_dir,
        ]

        self.logger.info("Running rdfind to remove duplicates...")

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        self.current_process = process

        stdout, stderr = process.communicate()

        self.current_process = None

        if self.cancelled:
            self.logger.info("rdfind was cancelled")
            return False

        if process.returncode == 0:
            self.logger.info("rdfind completed successfully - duplicates removed")
            return True
        else:
            self.logger.warning(f"rdfind failed with return code {process.returncode}")
            if stderr:
                self.logger.warning(f"rdfind error: {stderr}")
            return False

    def cancel(self):
        self.cancelled = True
        if self.current_process:
            self.logger.info("Terminating rdfind process")
            try:
                self.current_process.terminate()
                # Give it a moment to terminate gracefully
                try:
                    self.current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # If it doesn't terminate, kill it
                    self.current_process.kill()
            except Exception as e:
                self.logger.error(f"Failed to terminate rdfind process: {e}")
