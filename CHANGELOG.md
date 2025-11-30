# Changelog

## [Unreleased]

## [v0.2.0] - 2025-11-30

### Added
- File type selection dialog with more categories
- Expandable category rows with individual switches
- Category-level switches to enable/disable all file types in a category at once
- Search functionality to filter file types
- Select All / Unselect All buttons for quick selection changes
- Smart PhotoRec command generation (exclude mode when >50% selected, include mode when <50%) - needs testing

### Changed
- Reorganized file types
- Moved FILE_TYPES configuration to config.py

### Fixed
- Empty `no_extension` directory no longer created when no files without extensions exist
- PhotoRec `report.xml` file excluded from being moved to destination (content duplicated in photorec logs)

## [v0.1.2] - 2025-11-22

### Added
- AppStream metadata

## [v0.1.1] - 2025-11-22

### Changed
- Updated application icon to use full app ID (`com.github.koxt2.datarecovery`)
- About dialog now displays correct application icon

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


