# Copyright 2025 Richard Potts
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
        "save_image": window.save_image_switch.get_active(),
        "keep_corrupted": window.corrupted_switch.get_active(),
        "remove_duplicates": window.dupes_switch.get_active(),
        "selected_extensions": [],
    }

    # Write file type selections to ~/.photorec.cfg and get selected extensions
    if window.file_types_dialog is not None:
        window.file_types_dialog.write_photorec_cfg()
        settings["selected_extensions"] = window.file_types_dialog.get_selected_file_types()

    return settings
