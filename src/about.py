# about.py
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

from gi.repository import Adw, Gtk
from .config import VERSION


about_dialog = Adw.AboutDialog(
    application_name='Data Recovery',
    application_icon='datarecovery',
    website='https://github.com/koxt2/datarecovery',
    issue_url='https://github.com/koxt2/datarecovery/issues',
    developer_name='koxt2',
    version=VERSION,
    copyright='© 2025 koxt2',
    license_type=Gtk.License.GPL_2_0
)

about_dialog.add_legal_section(
    'PhotoRec',
    '© CGSecurity',
    Gtk.License.GPL_2_0,
    'https://www.cgsecurity.org/wiki/PhotoRec'
)

about_dialog.add_legal_section(
    'rdfind',
    '© Paul Dreik',
    Gtk.License.GPL_2_0,
    'https://rdfind.pauldreik.se/'
)

about_dialog.add_legal_section(
    'ddrescue',
    '© GNU Project',
    Gtk.License.GPL_3_0,
    'https://www.gnu.org/software/ddrescue/'
)

about_dialog.add_acknowledgement_section(
    'Acknowledgements',
    [
        'photorec - https://www.cgsecurity.org/wiki/PhotoRec',
        'rdfind - https://rdfind.pauldreik.se/',
        'ddrescue - https://www.gnu.org/software/ddrescue/'
    ]
)

