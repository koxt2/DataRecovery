# spec file for package datarecovery (RPM-only)
# Simplified for OBS RPM builds

Name:           datarecovery
Version:        _auto_
Release:        0
Summary:        GTK4/Libadwaita application for data recovery
License:        GPL-2.0-or-later
BuildArch:      noarch
Group:          System/Archiving
URL:            https://github.com/koxt2/DataRecovery
Source:         %{name}-%{version}.tar.xz
Source1:        _service

BuildRequires:  meson >= 1.0.0
BuildRequires:  pkgconfig
BuildRequires:  python3-devel
BuildRequires:  pkgconfig(gtk4)
BuildRequires:  pkgconfig(libadwaita-1)
BuildRequires:  pkgconfig(gio-2.0)
BuildRequires:  desktop-file-utils

Requires:       python3
Requires:       python3-gobject
Requires:       typelib(Gtk) = 4.0
Requires:       typelib(Adw) = 1
Requires:       gnu_ddrescue
Requires:       photorec
Requires:       rdfind
Requires:       udisks2
Requires:       polkit
Requires:       hicolor-icon-theme
Requires:       dbus-1-common

%description
A GTK4/Libadwaita application for data recovery using ddrescue and PhotoRec. Recovers all files (not just deleted ones) from storage devices or disk images, organizes them by file type, and optionally removes duplicates using rdfind.

%prep
%autosetup

%build
%meson
%meson_build

%install
%meson_install

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/datarecovery.desktop

%files
%license LICENSE
%doc README.md
%{_bindir}/datarecovery
%{_bindir}/datarecovery-pkexec-helper
%{_datadir}/datarecovery/
%{_datadir}/applications/datarecovery.desktop
%{_datadir}/dbus-1/services/com.github.koxt2.datarecovery.service
%{_datadir}/icons/hicolor/*/apps/com.github.koxt2.datarecovery*.*
%{_datadir}/metainfo/com.github.koxt2.datarecovery.metainfo.xml
%{_datadir}/polkit-1/actions/datarecovery.policy

%changelog
* Tue Apr 28 2026 koxt2 <koxt2@protonmail.com> - 0.5.0
- Progress bar updates while recovering data and organising files
- New `utils.py` module with shared `format_bytes` and `format_size` functions
- Disk space check now also runs when recovering from an image file (previously only ran for physical devices)
- Logs are now always generated and saved to destination (no longer optional)
- This was needed so that photorec progress can be displayed
- Application no longer re-initialises when brought back to the foreground (subsequent activations now just re-present the existing window)
- `MountedPartitionChecker` no longer takes an unused `device_dropdown` parameter
- `PartitionRow.type` property renamed to `part_type` to avoid shadowing the Python built-in
- README update
- Duplicate `/d` flag in PhotoRec command that would confuse file output location
- Bare `except:` clauses replaced with `except OSError:` in three places to avoid swallowing unexpected exceptions
- Redundant module-level loggers in `imager.py` removed (class already creates its own)
- Duplicate `universal_newlines=True` kwarg removed from `subprocess.Popen` call in `imager.py` (`text=True` is the same thing)
- Unused `DDRESCUE_RETRY_PASSES` import removed from `imager.py`
- Unused `os` import removed from `block_devices.py`
- Silently-swallowed file dialog exception in `window.py` is now logged
- Duplicate `_format_bytes` method removed from `DeviceImager` and `RecoveryWorkflow`; both now use `utils.format_bytes`
- Wrong file name in `initializer.py` header comment (`main.py` → `initializer.py`)
- Removed redundant internal `GLib.idle_add` wrapping in `RecoveryProgressDialog` methods; callers already schedule on the main thread
- Updated screenshots

* Sat Dec 27 2025 koxt2 <koxt2@protonmail.com> - 0.4.1
- Updated screenshots

* Tue Dec 23 2025 koxt2 <koxt2@protonmail.com> - 0.4.0
- SMART data monitoring with health indicators in device columnview
- Detailed SMART attributes viewer showing all available drive metrics
- Fixed bug where lsblk returning multiple lines for device size caused parsing error
- File renamed: initialiser.py → initializer.py for consistent American spelling
- Window method renamed: initialize() → setup_window() for clarity
- Removed unused imports across multiple files

* Fri Dec 19 2025 koxt2 <koxt2@protonmail.com> - 0.3.0
- Custom signature dialog for defining PhotoRec file signatures
- Support for adding, viewing, and deleting custom file signatures
- Custom signatures integrated into file types dialog under "System & Other" category
- Application now uses ~/.photorec.sig for storing custom file signatures
- Application now writes to ~/.photorec.cfg for PhotoRec file type configuration
- Reorganised file types dialog
- Moved FILE_TYPES and FILE_TYPE_GROUPS to dedicated file_types.py module for better organization
- File type search now uses PhotoRec family keys instead of extensions for accurate matching

* Sun Nov 30 2025 koxt2 <koxt2@protonmail.com> - 0.2.0
- File type selection dialog with more categories
- Expandable category rows with individual switches
- Category-level switches to enable/disable all file types in a category at once
- Search functionality to filter file types
- Select All / Unselect All buttons for quick selection changes
- Smart PhotoRec command generation (exclude mode when >50% selected, include mode when <50%) - needs testing
- Reorganized file types
- Moved FILE_TYPES configuration to config.py
- Empty `no_extension` directory no longer created when no files without extensions exist
- PhotoRec `report.xml` file excluded from being moved to destination (content duplicated in photorec logs)

* Sat Nov 22 2025 koxt2 <koxt2@protonmail.com> - 0.1.2
- AppStream metadata

* Sat Nov 22 2025 koxt2 <koxt2@protonmail.com> - 0.1.1
- Updated application icon to use full app ID (com.github.koxt2.datarecovery)
- About dialog now displays correct application icon

* Thu Nov 20 2025 koxt2 <koxt2@protonmail.com> - 0.1.0
- Initial release of datarecovery application
- GTK4/Libadwaita-based user interface for data recovery
- Integration with ddrescue for disk imaging
- Integration with PhotoRec for file recovery
- Automatic file organization by type
- Duplicate file detection and removal using rdfind
- Disk space checking before imaging and recovery operations
- Support for both storage devices and disk images
- Polkit integration for elevated permissions
- Multi-distro packaging support (RPM, DEB, Arch Linux)
