# utils.py
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


def format_bytes(bytes_value):
    """Convert a byte count to a human-readable string (e.g. '1.5 GB')."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def format_size(size_bytes):
    """Format a byte count for storage display (MB/GB, 2 decimal places)."""
    if not size_bytes:
        return "0 MB"
    size_mb = size_bytes / (1024 * 1024)
    if size_mb > 1000:
        return f"{size_mb / 1024:.2f} GB"
    return f"{size_mb:.2f} MB"
