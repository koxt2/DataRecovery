# config.py
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

"""
Configuration constants for the Data Recovery application.
Centralizes all hardcoded values and magic numbers.
"""

# Application version (set by meson during build)
VERSION = '@VERSION@'

# Directory and file names
RECOVERY_DATA_FOLDER = "Recovery Data"
WORKING_DIR_NAME = "working"
RECOVERED_FILES_DIR = "recovered_files"

# Log file names
DATARECOVERY_LOG = "datarecovery.log"
IMAGER_LOG = "imager_output.log"
PHOTOREC_LOG_PREFIX = "photorec_"
DUPLICATES_LOG = "duplicates.log"

# File extensions
IMAGE_FILE_EXTENSION = ".img"
MAP_FILE_EXTENSION = ".map"
LOG_FILE_EXTENSION = ".log"

# ddrescue settings
DDRESCUE_RETRY_PASSES = 3
DISK_SPACE_SAFETY_MARGIN_PERCENT = 0.10  # 10%

# Tool names (for dependency checking)
REQUIRED_TOOLS = ['ddrescue', 'photorec', 'rdfind', 'udisksctl']

# PhotoRec options
PHOTOREC_OPTIONS_BASE = "options"
PHOTOREC_OPTION_KEEP_CORRUPTED = "keep_corrupted_file"
PHOTOREC_OPTION_SEARCH = "search"
