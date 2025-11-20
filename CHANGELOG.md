# Changelog

## [Unreleased]

## [v0.1.0] - 2025-11-20

### Added
- Initial release of DataRecovery application
- GTK4/Libadwaita user interface
- Device selection with UDisks2 integration
- Disk imaging with GNU ddrescue
- File recovery using PhotoRec
- Automatic file organization by extension
- Corrupted file separation (files starting with 'b')
- Duplicate file removal with rdfind
- Mount detection and system partition protection
- Optional disk image and log saving
- pkexec integration for privileged operations
- Comprehensive logging system
- Disk space checking before imaging and recovery
- 10% safety margin for disk space calculations to prevent out-of-space errors
- Cleanup of incomplete image files on imaging failure
- Multi-distro packaging support (RPM, DEB, Arch Linux)

### Security
- Whitelist-based path validation for privileged operations
- System partition detection to prevent running on active system drives
- UID/GID validation for file ownership


