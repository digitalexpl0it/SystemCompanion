# System Companion Flatpak

This directory contains the Flatpak packaging configuration for System Companion.

## 📦 What is Flatpak?

Flatpak is a system for building, distributing, installing, and managing applications on Linux. It provides a sandbox environment that isolates applications from the rest of the system while providing access to the resources they need.

## 🚀 Quick Start

### Prerequisites

1. **Install Flatpak** (if not already installed):
   ```bash
   sudo apt install flatpak
   ```

2. **Install Flatpak Builder**:
   ```bash
   sudo apt install flatpak-builder
   ```

3. **Add Flathub repository** (for additional runtimes):
   ```bash
   flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
   ```

### Building the Flatpak

1. **Navigate to the Flatpak directory**:
   ```bash
   cd packaging/flatpak
   ```

2. **Run the build script**:
   ```bash
   ./build.sh
   ```

   This will:
   - Install required GNOME runtimes
   - Build the Flatpak package
   - Create a distributable bundle

### Installing the Flatpak

#### Option 1: Install from bundle
```bash
flatpak install --user system-companion-0.1.0.flatpak
```

#### Option 2: Install from local repository
```bash
flatpak install --user --sideload-repo=repo org.systemcompanion.app
```

#### Option 3: Install from remote repository (when published)
```bash
flatpak install org.systemcompanion.app
```

### Running the Application

```bash
flatpak run org.systemcompanion.app
```

## 📁 File Structure

```
packaging/flatpak/
├── org.systemcompanion.app.yml      # Main Flatpak manifest
├── org.systemcompanion.app.desktop  # Desktop entry file
├── org.systemcompanion.app.metainfo.xml  # AppStream metadata
├── build.sh                         # Build script
└── README.md                        # This file
```

## 🔧 Configuration Details

### Manifest File (`org.systemcompanion.app.yml`)

The manifest file defines:
- **App ID**: `org.systemcompanion.app`
- **Runtime**: GNOME Platform 45
- **SDK**: GNOME SDK 45
- **Permissions**: Network, IPC, display, audio, file system access
- **Dependencies**: Python packages (psutil, py-cpuinfo, GPUtil, netifaces)
- **Installation**: Application files, icons, desktop entry, metadata

### Permissions

The Flatpak includes the following permissions:
- **Network access**: For system monitoring and updates
- **Display access**: For GUI rendering (X11/Wayland)
- **Audio access**: For system notifications
- **File system access**: For configuration and data storage
- **Device access**: For hardware monitoring (DRI, input devices)

### Sandboxing

The application runs in a sandboxed environment that:
- **Isolates** the app from the system
- **Provides** necessary access to system resources
- **Protects** user privacy and system security
- **Ensures** consistent behavior across distributions

## 🛠️ Development

### Modifying the Manifest

To modify the Flatpak configuration:

1. **Edit the manifest file** (`org.systemcompanion.app.yml`)
2. **Update dependencies** if needed
3. **Modify permissions** if required
4. **Rebuild** using the build script

### Adding New Dependencies

To add new Python dependencies:

1. **Add a new module** to the manifest:
   ```yaml
   - name: python3-newpackage
     buildsystem: simple
     build-commands:
       - pip3 install --prefix=/app newpackage
     sources:
       - type: file
         url: https://files.pythonhosted.org/packages/.../newpackage-1.0.0.tar.gz
         sha256: <checksum>
   ```

2. **Update the build script** if needed
3. **Rebuild** the Flatpak

### Testing Changes

1. **Build** the Flatpak: `./build.sh`
2. **Install** the new version: `flatpak install --user --sideload-repo=repo org.systemcompanion.app`
3. **Test** the application: `flatpak run org.systemcompanion.app`
4. **Uninstall** if needed: `flatpak uninstall org.systemcompanion.app`

## 📦 Distribution

### Publishing to Flathub

To publish to Flathub:

1. **Fork** the [Flathub repository](https://github.com/flathub/flathub)
2. **Add** your application manifest
3. **Submit** a pull request
4. **Wait** for review and approval

### Self-Hosting

To host your own Flatpak repository:

1. **Set up** a web server
2. **Upload** the repository files
3. **Configure** the repository URL
4. **Share** the installation instructions

## 🔍 Troubleshooting

### Common Issues

#### Build Failures
- **Check** that all dependencies are available
- **Verify** file paths in the manifest
- **Ensure** Flatpak runtimes are installed

#### Runtime Issues
- **Check** permissions in the manifest
- **Verify** file system access
- **Review** sandbox restrictions

#### Installation Issues
- **Ensure** Flatpak is properly installed
- **Check** repository configuration
- **Verify** bundle integrity

### Debugging

#### Enable Debug Output
```bash
flatpak run --log-level=debug org.systemcompanion.app
```

#### Check Application Logs
```bash
flatpak run --command=journalctl org.systemcompanion.app
```

#### Inspect Sandbox
```bash
flatpak run --command=bash org.systemcompanion.app
```

## 📚 Resources

- [Flatpak Documentation](https://docs.flatpak.org/)
- [Flathub Guidelines](https://github.com/flathub/flathub/wiki/App-Requirements)
- [GNOME Platform](https://developer.gnome.org/platform/)
- [AppStream Specification](https://www.freedesktop.org/software/appstream/docs/)

## 🤝 Contributing

When contributing to the Flatpak packaging:

1. **Test** your changes thoroughly
2. **Update** documentation as needed
3. **Follow** Flathub guidelines
4. **Submit** pull requests for review

---

For more information about System Companion, see the [main documentation](../../docs/README.md). 