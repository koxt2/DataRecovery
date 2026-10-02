# Copyright 2025 Richard Potts
# SPDX-License-Identifier: GPL-2.0-or-later

# Application version (set by meson during build)
VERSION = "@VERSION@"

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
REQUIRED_TOOLS = ["ddrescue", "photorec", "rdfind", "udisksctl"]

# PhotoRec options
PHOTOREC_OPTIONS_BASE = "options"
PHOTOREC_OPTION_KEEP_CORRUPTED = "keep_corrupted_file"
PHOTOREC_OPTION_SEARCH = "search"

CRITICAL_ATTRIBUTES = {
    5: ("Reallocated_Sector_Ct", 10),  # threshold: warn if > 10
    10: ("Spin_Retry_Count", 5),  # threshold: warn if > 5
    187: ("Reported_Uncorrect", 0),  # threshold: warn if > 0
    188: ("Command_Timeout", 100),  # threshold: warn if > 100
    196: ("Reallocated_Event_Count", 10),  # threshold: warn if > 10
    197: ("Current_Pending_Sector", 0),  # threshold: warn if > 0
    198: ("Offline_Uncorrectable", 0),  # threshold: warn if > 0
}
