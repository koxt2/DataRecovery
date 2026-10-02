# Copyright 2025 Richard Potts
# SPDX-License-Identifier: GPL-2.0-or-later

from gi.repository import Adw, Gtk

from .config import VERSION

about_dialog = Adw.AboutDialog(
    application_name="Data Recovery",
    application_icon="com.github.koxt2.datarecovery",
    website="https://github.com/koxt2/datarecovery",
    issue_url="https://github.com/koxt2/datarecovery/issues",
    developer_name="Richard Potts",
    version=VERSION,
    copyright="© 2025 Richard Potts",
    license_type=Gtk.License.GPL_2_0,
)

about_dialog.add_legal_section(
    "PhotoRec",
    "© CGSecurity",
    Gtk.License.GPL_2_0,
    "https://www.cgsecurity.org/wiki/PhotoRec",
)

about_dialog.add_legal_section(
    "rdfind", "© Paul Dreik", Gtk.License.GPL_2_0, "https://rdfind.pauldreik.se/"
)

about_dialog.add_legal_section(
    "ddrescue",
    "© GNU Project",
    Gtk.License.GPL_3_0,
    "https://www.gnu.org/software/ddrescue/",
)

about_dialog.add_acknowledgement_section(
    "Acknowledgements",
    [
        "photorec - https://www.cgsecurity.org/wiki/PhotoRec",
        "rdfind - https://rdfind.pauldreik.se/",
        "ddrescue - https://www.gnu.org/software/ddrescue/",
    ],
)
