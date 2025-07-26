# System Companion AppImage

This directory contains the AppImage packaging configuration for System Companion.

## 📦 What is AppImage?

AppImage is a format for distributing portable software on Linux without needing superuser permissions to install the application. It allows developers to package their applications in a way that works across different Linux distributions.

## 🚀 Quick Start

### Prerequisites

1. **Install required system packages**:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv wget
   ```

2. **Install GTK4 development libraries** (if not already installed):
   ```bash
   sudo apt install -y libgtk-4-dev libadwaita-1-dev python3-gi python3-gi-cairo
   ```

### Building the AppImage

1. **Navigate to the AppImage directory**:
   ```bash
   cd packaging/appimage
   ```

2. **Run the build script**:
   ```bash
   ./build.sh
   ```

   This will:
   - Download and install appimagetool if needed
   - Create the AppDir structure
   - Copy application files and dependencies
   - Bundle everything into an AppImage

### Using the AppImage

#### Make it executable
```bash
chmod +x dist/System_Companion-0.1.0-x86_64.AppImage
```

#### Run the application
```bash
./dist/System_Companion-0.1.0-x86_64.AppImage
```

#### Install to system (optional)
```bash
# Copy to a permanent location
sudo cp dist/System_Companion-0.1.0-x86_64.AppImage /usr/local/bin/system-companion

# Make it executable
sudo chmod +x /usr/local/bin/system-companion

# Run from anywhere
system-companion
```

## 📁 File Structure

```
packaging/appimage/
├── AppDir/
│   ├── AppRun                    # AppImage launcher script
│   ├── system-companion.desktop  # Desktop entry file
│   └── usr/                      # Application files
│       ├── bin/                  # Executables
│       ├── lib/                  # Libraries
│       └── share/                # Data files
├── build.sh                      # Build script
└── README.md                     # This file
```

## 🔧 How AppImage Works

### AppDir Structure
The AppDir contains all the files needed to run the application:
- **AppRun**: The launcher script that sets up the environment
- **Desktop file**: For desktop integration
- **Application files**: Python code, libraries, and resources
- **Dependencies**: All required Python packages and system libraries

### Environment Setup
The AppRun script:
- **Sets up Python path** to find the application
- **Configures GTK4** environment variables
- **Creates necessary directories** for configuration and data
- **Launches the application** with proper environment

### Library Bundling
The build script bundles:
- **Python dependencies** (psutil, py-cpuinfo, GPUtil, netifaces)
- **GTK4 libraries** and bindings
- **System libraries** required for the application
- **Application resources** (icons, CSS, etc.)

## 🛠️ Development

### Modifying the Build

To modify the AppImage build:

1. **Edit the build script** (`build.sh`)
2. **Update dependencies** if needed
3. **Modify AppRun** for environment changes
4. **Rebuild** using the build script

### Adding New Dependencies

To add new Python dependencies:

1. **Add to the pip install command** in `build.sh`:
   ```bash
   pip install --target="$APP_DIR/usr/lib/python3.11/site-packages" \
       psutil>=5.9.0 \
       py-cpuinfo>=9.0.0 \
       GPUtil>=1.4.0 \
       netifaces>=0.11.0 \
       newpackage>=1.0.0
   ```

2. **Rebuild** the AppImage

### Testing Changes

1. **Build** the AppImage: `./build.sh`
2. **Test** the application: `./dist/System_Companion-0.1.0-x86_64.AppImage`
3. **Verify** functionality works correctly
4. **Iterate** as needed

## 📦 Distribution

### Advantages of AppImage

- **Portable**: Runs on most Linux distributions
- **No installation**: Just download and run
- **Self-contained**: Includes all dependencies
- **Easy distribution**: Single file to share
- **No root access**: Runs without system modifications

### Distribution Options

#### Direct Distribution
- **Share the .AppImage file** directly
- **Upload to GitHub releases**
- **Host on your own server**
- **Distribute via email or USB**

#### AppImageHub
- **Submit to AppImageHub** for discovery
- **Get listed in app catalogs**
- **Automatic updates** via AppImageUpdate

#### GitHub Releases
- **Create releases** with AppImages
- **Automatic downloads** for users
- **Version management** and changelog

## 🔍 Troubleshooting

### Common Issues

#### AppImage Won't Run
- **Check permissions**: `chmod +x filename.AppImage`
- **Verify architecture**: Ensure it's built for your system (x86_64)
- **Check dependencies**: Some system libraries may be missing

#### Missing Libraries
- **Install system dependencies**:
  ```bash
  sudo apt install -y libgtk-4-1 libadwaita-1-0 libglib-2.0-0
  ```

#### Python Import Errors
- **Check Python version**: AppImage uses Python 3.11
- **Verify bundled packages**: All dependencies should be included
- **Check PYTHONPATH**: AppRun sets this correctly

### Debugging

#### Run with Verbose Output
```bash
./System_Companion-0.1.0-x86_64.AppImage --verbose
```

#### Extract AppImage for Inspection
```bash
# Extract the AppImage
./System_Companion-0.1.0-x86_64.AppImage --appimage-extract

# Inspect the contents
ls squashfs-root/
```

#### Check AppImage Integrity
```bash
# Verify the AppImage
./System_Companion-0.1.0-x86_64.AppImage --appimage-validate
```

## 🔄 Updates

### AppImageUpdate
Users can update AppImages automatically:

```bash
# Install AppImageUpdate
sudo apt install appimageupdate

# Update the AppImage
appimageupdate System_Companion-0.1.0-x86_64.AppImage
```

### Continuous Integration
For automated builds:

1. **Set up GitHub Actions** to build AppImages
2. **Upload to releases** automatically
3. **Notify users** of new versions
4. **Maintain update feeds** for AppImageUpdate

## 📚 Resources

- [AppImage Documentation](https://docs.appimage.org/)
- [AppImageKit](https://github.com/AppImage/AppImageKit)
- [AppImageHub](https://appimage.github.io/)
- [AppImageUpdate](https://github.com/AppImage/AppImageUpdate)

## 🤝 Contributing

When contributing to the AppImage packaging:

1. **Test** your changes thoroughly
2. **Verify** the AppImage runs on different distributions
3. **Update** documentation as needed
4. **Follow** AppImage best practices

## 🆚 Comparison with Other Formats

| Feature | AppImage | Flatpak | Snap |
|---------|----------|---------|------|
| **Portability** | ✅ High | ⚠️ Medium | ⚠️ Medium |
| **Installation** | ✅ None | ✅ Easy | ✅ Easy |
| **Dependencies** | ✅ Bundled | ✅ Runtime | ✅ Bundled |
| **Updates** | ✅ Manual/Auto | ✅ Automatic | ✅ Automatic |
| **Sandboxing** | ❌ None | ✅ Full | ✅ Full |
| **Size** | ⚠️ Large | ✅ Small | ⚠️ Large |

---

For more information about System Companion, see the [main documentation](../../docs/README.md). 