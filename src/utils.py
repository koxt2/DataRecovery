# Copyright 2025 Richard Potts
# SPDX-License-Identifier: GPL-2.0-or-later


def format_bytes(bytes_value):
    """Convert a byte count to a human-readable string (e.g. '1.5 GB')."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
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
