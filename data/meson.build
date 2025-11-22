# Process desktop file
desktop_file = configure_file(
  input: 'datarecovery.desktop.in',
  output: 'datarecovery.desktop',
  copy: true,
  install: true,
  install_dir: get_option('datadir') / 'applications'
)

install_data('datarecovery.policy',
  install_dir: get_option('datadir') / 'polkit-1' / 'actions')

# Install AppStream metadata
install_data('com.github.koxt2.datarecovery.metainfo.xml',
  install_dir: get_option('datadir') / 'metainfo')

# Install pkexec helper script
install_data('datarecovery-pkexec-helper',
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x')

# Configure and install D-Bus service file
conf = configuration_data()
conf.set('APP_ID', 'com.github.koxt2.datarecovery')
conf.set('bindir', get_option('prefix') / get_option('bindir'))

configure_file(
  input: 'com.github.koxt2.datarecovery.service.in',
  output: 'com.github.koxt2.datarecovery.service',
  configuration: conf,
  install: true,
  install_dir: get_option('datadir') / 'dbus-1' / 'services'
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args: [desktop_file])
endif

subdir('icons')
