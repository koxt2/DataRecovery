# Changelog

## [Unreleased]

## [v0.4.0] - 2025-12-23
### Added
- SMART data monitoring with health indicators in device columnview
- Detailed SMART attributes viewer showing all available drive metrics

### Fixed
- Fixed bug where `lsblk` returning multiple lines for device size caused parsing error
- File renamed: `initialiser.py` → `initializer.py` for consistent American spelling
- Window method renamed: `initialize()` → `setup_window()` for clarity
- Removed unused imports across multiple files

## [v0.3.0] - 2025-12-19

### Added
- Custom signature dialog for defining PhotoRec file signatures
- Support for adding, viewing, and deleting custom file signatures
- Custom signatures integrated into file types dialog under "System & Other" category
- Application now uses `~/.photorec.sig` for storing custom file signatures
- Application now writes to `~/.photorec.cfg` for PhotoRec file type configuration

### Changed
- Reorganised file types dialog
- Moved FILE_TYPES and FILE_TYPE_GROUPS to dedicated file_types.py module for better organization
- Custom signatures now appear in "System & Other" group in file types dialog

### Fixed
- File type search now uses PhotoRec family keys instead of extensions for accurate matching (e.g., searching for "py" now correctly finds files recovered under the "txt" family)

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


