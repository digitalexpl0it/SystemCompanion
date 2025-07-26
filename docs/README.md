# System Companion Documentation

Welcome to the System Companion documentation. This directory contains detailed documentation for various aspects of the application.

## 📚 Documentation Index

### 🎯 Core Documentation

#### [Main README](../README.md)
The main project README with overview, features, installation instructions, and quick start guide.

### 🔧 Development Documentation

#### [Development Guide](development_guide.md)
Comprehensive guide for developers contributing to System Companion:
- Project architecture and component overview
- Development setup and environment configuration
- Code style guidelines and best practices
- Testing procedures and debugging techniques
- UI development patterns and GTK4 guidelines

#### [CPU Mini Graphs Improvements](cpu_mini_graphs_improvements.md)
Detailed documentation about the CPU monitoring mini-graphs implementation, including:
- Real-time CPU usage visualization
- Multi-core performance tracking
- Performance optimization techniques
- UI/UX considerations for CPU monitoring

#### [Disk I/O Performance Charts](disk_iops_chart_improvements.md)
Comprehensive guide to disk performance monitoring features:
- I/O operations per second tracking
- Disk read/write speed monitoring
- Storage health indicators
- Performance bottleneck detection

#### [Multi-Interface Network Charts](multi_interface_network_chart_improvements.md)
Documentation for advanced network monitoring capabilities:
- Multi-interface network tracking
- Bandwidth usage analysis
- Network performance optimization
- Real-time network statistics

### 🚀 Quick Reference

#### Development Setup
```bash
# Clone and setup
git clone https://github.com/yourusername/system-companion.git
cd system-companion
./scripts/setup_dev_environment.sh

# Run the application
python3 run.py
```

#### Key Directories
- `src/` - Main application source code
- `resources/` - UI resources, icons, and CSS
- `tests/` - Test suite
- `build-aux/` - Build system files
- `packaging/` - Distribution files

#### Technology Stack
- **Frontend**: GTK4 + libadwaita (Python PyGObject)
- **Backend**: Python 3.11+
- **System Integration**: psutil, py-cpuinfo, systemd APIs
- **Data**: SQLite for local storage, JSON for config
- **Build**: Meson + Ninja

### 📖 Contributing to Documentation

When adding new documentation:

1. **Create new .md files** in this `docs/` directory
2. **Update this README.md** to include links to new documentation
3. **Follow the naming convention**: `feature_name_description.md`
4. **Use descriptive titles** and clear structure
5. **Include code examples** where relevant

### 🔗 External Resources

- [GTK4 Documentation](https://docs.gtk.org/gtk4/)
- [libadwaita Documentation](https://gnome.pages.gitlab.gnome.org/libadwaita/)
- [Python PyGObject](https://pygobject.readthedocs.io/)
- [GNOME Human Interface Guidelines](https://developer.gnome.org/hig/)

### 📝 Documentation Standards

- Use clear, concise language
- Include code examples where helpful
- Maintain consistent formatting
- Update documentation when features change
- Include screenshots for UI-related documentation

---

**Need help?** Check the [main README](../README.md) for installation and setup instructions, or open an issue on GitHub for support. 