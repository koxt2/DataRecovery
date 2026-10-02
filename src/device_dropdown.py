# Copyright 2025 Richard Potts
# SPDX-License-Identifier: GPL-2.0-or-later

from gi.repository import Gtk

from .block_devices import get_block_devices

SELECTION_NO_DEVICE = 0
SELECTION_IMAGE_FILE = 1
SELECTION_FIRST_DEVICE = 2


class DeviceDropdown:
    def __init__(self, window):
        self.window = window
        self.is_refreshing = False  # Flag to prevent triggering on_device_selected during refresh
        self.populate_device_selector()

    def populate_device_selector(self):
        self.window.device_liststore.remove_all()
        self.devices, self.partitions = get_block_devices()
        self.window.device_liststore.append(Gtk.StringObject.new("Select a device..."))
        self.window.device_liststore.append(Gtk.StringObject.new("Select image file..."))

        for device in self.devices:
            device_label = self._format_device_label(device)
            self.window.device_liststore.append(Gtk.StringObject.new(device_label))

        self.window.select_device_dropdown.set_selected(SELECTION_NO_DEVICE)
        return True

    def _format_device_label(self, device):
        label = device["path"]
        details = []
        if device.get("model"):
            details.append(str(device["model"]))
        if device.get("serial"):
            details.append(str(device["serial"]))
        if details:
            label += " (" + " ".join(details) + ")"
        return label

    def get_device_from_selection(self, selection_index):
        if selection_index < SELECTION_FIRST_DEVICE:
            return None

        device_index = selection_index - SELECTION_FIRST_DEVICE
        if device_index < len(self.devices):
            return self.devices[device_index]

        return None

    def get_selection_index_for_device_path(self, device_path):
        for i, device in enumerate(self.devices):
            if device["path"] == device_path:
                return i + SELECTION_FIRST_DEVICE
        return None

    def refresh_with_selection_preserved(self):
        current_selection = self.window.select_device_dropdown.get_selected()

        current_device = self.get_device_from_selection(current_selection)
        selected_device_path = current_device["path"] if current_device else None

        self.is_refreshing = True

        # Refresh the dropdown
        self.populate_device_selector()

        if selected_device_path:
            restored_index = self.get_selection_index_for_device_path(selected_device_path)
            if restored_index is not None:
                self.window.select_device_dropdown.set_selected(restored_index)
                self.is_refreshing = False
                return True

        # If device no longer exists, try to restore selection by index
        max_selection = len(self.devices) + SELECTION_FIRST_DEVICE - 1
        if current_selection <= max_selection:
            self.window.select_device_dropdown.set_selected(current_selection)
        else:
            # Reset to default if selection is now out of range
            self.window.select_device_dropdown.set_selected(SELECTION_NO_DEVICE)

        self.is_refreshing = False
        return True

    def add_image_to_selector(self, path):

        # Check if image is already in the list
        for i in range(self.window.device_liststore.get_n_items()):
            if self.window.device_liststore.get_item(i).get_string() == path:
                self.window.select_device_dropdown.set_selected(i)
                # Update window state for selected image
                self.window.device_path = path
                return True

        self.window.device_liststore.append(Gtk.StringObject.new(path))
        self.window.select_device_dropdown.set_selected(
            self.window.device_liststore.get_n_items() - 1
        )

        # Update window state for selected image
        self.window.device_path = path
        return True
