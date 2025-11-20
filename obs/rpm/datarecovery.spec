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
%if 0%{?fedora}
Requires:       gtk4
Requires:       libadwaita
Requires:       ddrescue
Requires:       testdisk
%else
Requires:       typelib(Gtk) = 4.0
Requires:       typelib(Adw) = 1
Requires:       gnu_ddrescue
Requires:       photorec
%endif
Requires:       rdfind
Requires:       udisks2
Requires:       polkit

%description
A GTK4/Libadwaita application for data recovery using ddrescue and PhotoRec. Recovers all files (not just deleted ones) from storage devices or disk images, organises them by file type, and optionally removes duplicates using rdfind.

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
%{_datadir}/icons/hicolor/*/apps/datarecovery*.*
%{_datadir}/polkit-1/actions/datarecovery.policy

%changelog
* Wed Nov 20 2025 koxt2 <koxt2@protonmail.com> - 0.1.0
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
