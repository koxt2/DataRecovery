pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'datarecovery'
gnome = import('gnome')

gnome.compile_resources('datarecovery',
  'datarecovery.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'datarecovery.in',
  output: 'datarecovery',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)

configure_file(
  input: 'config.py',
  output: 'config.py',
  configuration: conf,
  install: true,
  install_dir: moduledir
)

datarecovery_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'log.py',
  'initialiser.py',
  'partition_guids.py',
  'block_devices.py',
  'device_dropdown.py',
  'device_columnview.py',
  'about.py',
  'settings.py',
  'imager.py',
  'mounted_check.py',
  'recovery_dialog.py',
  'file_operations.py',
  'file_types_dialog.py',
  'recover.py',
  'duplicates.py',
  'recovery_workflow.py',
]

install_data(datarecovery_sources, install_dir: moduledir)