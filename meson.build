project('datarecovery',
          version: 'v0.1.2',
    meson_version: '>= 1.0.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

gnome = import('gnome')

subdir('data')
subdir('src')

gnome.post_install(
     glib_compile_schemas: true,
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)