# System Companion

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![GTK](https://img.shields.io/badge/GTK-4.0-green.svg)](https://www.gtk.org/)
[![License](https://img.shields.io/badge/License-GPL--3.0-orange.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Ubuntu%2022.04+-red.svg)](https://ubuntu.com/)

A fast, optimized, and beautiful system health & maintenance dashboard for Ubuntu Linux.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Technology Stack](#technology-stack)
- [Performance Targets](#performance-targets)
- [Installation](#installation)
- [Development](#development)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [License](#license)
- [Support](#support)

## Overview

System Companion consolidates scattered system monitoring and maintenance tools into a single, modern interface. It provides real-time system health monitoring, predictive maintenance alerts, intelligent cleanup recommendations, and performance optimization - all with a clean, intuitive design.

## Features

### Real-Time Health Monitoring
- CPU, memory, and disk usage with predictive analytics
- Temperature monitoring with thermal throttling alerts
- Battery health tracking (for laptops) with degradation warnings
- Network performance metrics and bandwidth analysis
- Process monitoring with resource usage breakdown

### Predictive Maintenance
- Disk health analysis using SMART data with failure prediction
- Memory leak detection and process optimization suggestions
- System performance degradation tracking over time
- Automated alerts for potential hardware issues

### Intelligent Cleanup & Optimization
- Automated temporary file cleanup with user approval
- Package cache management and orphaned package detection
- Log file rotation and management
- Startup application optimization
- Disk space analysis with large file identification

### Performance Insights
- System boot time tracking and optimization suggestions
- Application performance profiling
- Resource usage patterns and optimization recommendations
- Historical performance data with trend analysis

### Security & Privacy Monitoring
- System update status and security patch tracking
- User permission analysis and security recommendations
- Network connection monitoring and suspicious activity detection
- Privacy audit of installed applications

## Screenshots

*Screenshots will be added as the application develops*

## Quick Start

```bash
# Clone the repository
git clone https://github.com/DigitalExpl0it/system-companion.git
cd system-companion

# Run automated setup (recommended for fresh Ubuntu systems)
./scripts/setup_dev_environment.sh

# Start the application
python3 run.py
```

## Technology Stack

- **Frontend**: GTK4 + libadwaita (Python PyGObject)
- **Backend**: Python 3.11+
- **System Integration**: psutil, py-cpuinfo, systemd APIs
- **Data**: SQLite for local storage, JSON for config
- **Build**: Meson + Ninja
- **Testing**: pytest
- **Packaging**: Flatpak

## Performance Targets

- Application startup: < 2 seconds
- UI responsiveness: < 100ms for interactions
- Memory usage: < 100MB baseline
- CPU usage: < 5% when idle
- Real-time updates: < 1 second intervals

## Installation

### Prerequisites

- Ubuntu 22.04 LTS or later
- Python 3.11+
- GTK4 development libraries
- libadwaita-1 development libraries

### Quick Setup (Recommended)

For a fresh Ubuntu system, use our automated setup script:

```bash
# Clone the repository
git clone https://github.com/yourusername/system-companion.git
cd system-companion

# Run the setup script (this will install all dependencies)
./scripts/setup_dev_environment.sh
```

> **Note**: The setup script will automatically install all required system dependencies and Python packages.

### Manual Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/system-companion.git
cd system-companion
```

2. Check dependencies:
```bash
./scripts/check_dependencies.py
```

3. Install system dependencies:
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv meson ninja-build \
    libgtk-4-dev libadwaita-1-dev python3-gi python3-gi-cairo \
    gir1.2-gtk-4.0 gir1.2-adw-1 build-essential pkg-config \
    libcairo2-dev libpango1.0-dev libgirepository1.0-dev
```

4. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

5. Install Python dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .[dev]
```

6. Build the project:
```bash
meson setup build
cd build
ninja
```

7. Run the application:
```bash
# Using the launcher script (recommended)
python3 run.py

# Or directly from src directory
cd src && PYTHONPATH=. python3 system_companion/main.py
```

### Flatpak Installation

#### Build from Source
```bash
# Navigate to the Flatpak directory
cd packaging/flatpak

# Run the build script
./build.sh

# Install the built package
flatpak install --user system-companion-0.1.0.flatpak

# Run the application
flatpak run org.systemcompanion.app
```

#### Prerequisites for Building
```bash
# Install Flatpak and builder
sudo apt install flatpak flatpak-builder

# Add Flathub repository
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

> **Note**: The Flatpak package provides a sandboxed environment and will be available on Flathub once the application is ready for distribution.

### AppImage Installation

#### Build from Source
```bash
# Navigate to the AppImage directory
cd packaging/appimage

# Run the build script
./build.sh

# Make the AppImage executable
chmod +x dist/System_Companion-0.1.0-x86_64.AppImage

# Run the application
./dist/System_Companion-0.1.0-x86_64.AppImage
```

#### Prerequisites for Building
```bash
# Install required packages
sudo apt install -y python3-pip python3-venv wget libgtk-4-dev libadwaita-1-dev python3-gi python3-gi-cairo
```

> **Note**: AppImages are portable and can run on most Linux distributions without installation. They include all dependencies and can be shared as a single file.

## Development

### Project Structure

```
system_companion/
├── src/
│   ├── main.py                 # Application entry point
│   ├── core/                   # Core system monitoring
│   ├── ui/                     # GTK4 UI components
│   ├── data/                   # Data management
│   ├── utils/                  # Utility functions
│   └── plugins/                # Plugin system
├── resources/                  # UI resources, icons, CSS
├── tests/                      # Test suite
├── docs/                       # Documentation (see [docs/README.md](docs/README.md))
├── build-aux/                  # Build system files
└── packaging/                  # Distribution files
```

### Documentation

For detailed documentation, see the [docs/](docs/) directory:
- [Documentation Index](docs/README.md) - Overview of all documentation
- [CPU Monitoring](docs/cpu_mini_graphs_improvements.md) - CPU performance tracking
- [Disk I/O Monitoring](docs/disk_iops_chart_improvements.md) - Storage performance
- [Network Monitoring](docs/multi_interface_network_chart_improvements.md) - Network statistics

### Running Tests

```bash
pytest tests/
```

### Code Style

This project follows PEP 8 with additional guidelines for GTK4 development. Use the provided `.cursorrules` file for IDE configuration.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow the performance-first principle
- Keep dependencies minimal
- Implement proper error handling
- Write comprehensive tests
- Document all public APIs
- Follow GNOME Human Interface Guidelines

## Roadmap

### Phase 1: Core Monitoring (Current)
- Basic system monitoring (CPU, memory, disk)
- Simple UI with GTK4
- Real-time data display

### Phase 2: Advanced Features
- Predictive maintenance
- Intelligent cleanup
- Performance insights
- Security monitoring

### Phase 3: Enterprise Features
- Multi-system monitoring
- Centralized reporting
- Plugin system
- API for external integrations

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- GNOME Project for GTK4 and libadwaita
- Python community for excellent system monitoring libraries
- Ubuntu community for inspiration and feedback

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/system-companion/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/system-companion/discussions)
- **Documentation**: [docs/README.md](docs/README.md) - Complete documentation index

---

**System Companion** - Making Linux system management beautiful and efficient. 