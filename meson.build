project('system-companion', 'python',
  version: '0.1.0',
  license: 'GPL-3.0',
  meson_version: '>= 0.60.0',
  default_options: [
    'python.install_env=auto',
    'python.platlibdir=lib/python3/site-packages',
  ]
)

# Python dependency
py_mod = import('python')
py3 = py_mod.find_installation('python3', required: true)

# Check for required Python packages
py3.dependency('psutil', required: true)
py3.dependency('py-cpuinfo', required: true)
py3.dependency('GPUtil', required: true)
py3.dependency('netifaces', required: true)

# GTK4 and libadwaita dependencies
gtk4_dep = dependency('gtk4', version: '>= 4.0.0', required: true)
adw_dep = dependency('libadwaita-1', version: '>= 1.0.0', required: true)
gobject_dep = dependency('gobject-2.0', required: true)

# Python GObject introspection
pygobject_dep = dependency('pygobject-3.0', required: true)

# Subdirectories
subdir('src')
subdir('resources')
subdir('tests')

# Install configuration
install_data('resources/system-companion.desktop', install_dir: 'share/applications')
install_data('resources/system-companion.metainfo.xml', install_dir: 'share/metainfo')

# Install icons
install_data('resources/icons/scalable/apps/system-companion.svg',
  install_dir: 'share/icons/hicolor/scalable/apps'
)

# Install man page
install_man('docs/system-companion.1')

# Summary
summary({
  'Build type': get_option('buildtype'),
  'Python': py3.full_path(),
  'GTK4': gtk4_dep.version(),
  'libadwaita': adw_dep.version(),
}, section: 'Configuration') 