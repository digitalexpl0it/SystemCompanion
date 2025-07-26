# Development Guide

This guide provides essential information for developers contributing to System Companion.

## 🏗️ Project Architecture

### Core Components

#### `src/system_companion/`
- **`main.py`** - Application entry point and GTK4 app initialization
- **`core/`** - System monitoring and analysis engines
- **`ui/`** - GTK4 user interface components
- **`data/`** - Database and data management
- **`utils/`** - Configuration, logging, and utility functions
- **`plugins/`** - Extensible plugin system (future)

#### Key UI Widgets
- **`dashboard_widget.py`** - Main dashboard with tab navigation
- **`health_widget.py`** - System health monitoring
- **`performance_widget.py`** - Performance analysis and benchmarks
- **`maintenance_widget.py`** - System maintenance tasks
- **`security_widget.py`** - Security monitoring and fixes
- **`settings_widget.py`** - Application settings

## 🚀 Development Setup

### Prerequisites
```bash
# System dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv meson ninja-build \
    libgtk-4-dev libadwaita-1-dev python3-gi python3-gi-cairo \
    gir1.2-gtk-4.0 gir1.2-adw-1 build-essential pkg-config \
    libcairo2-dev libpango1.0-dev libgirepository1.0-dev
```

### Quick Start
```bash
# Clone and setup
git clone https://github.com/digitalexpl0it/SystemCompanion.git
cd SystemCompanion
./scripts/setup_dev_environment.sh

# Activate virtual environment
source venv/bin/activate

# Run the application
python3 run.py
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src/system_companion tests/

# Run specific test file
pytest tests/unit/test_config.py
```

### Test Structure
- **`tests/unit/`** - Unit tests for individual components
- **`tests/integration/`** - Integration tests for UI components
- **`tests/fixtures/`** - Test data and mock objects

## 📝 Code Style

### Python Guidelines
- Follow PEP 8 with 4-space indentation
- Use type hints for all function parameters and return values
- Keep functions under 50 lines
- Use descriptive variable and function names
- Add docstrings for all public functions and classes

### GTK4 Guidelines
- Use libadwaita widgets for modern appearance
- Implement proper signal handling
- Use CSS for styling (avoid inline styles)
- Follow GNOME Human Interface Guidelines
- Implement accessibility features

### Example Code Structure
```python
from typing import Optional
from gi.repository import Gtk, Adw

class ExampleWidget(Gtk.Box):
    """Example widget demonstrating best practices."""
    
    def __init__(self, parent: Optional[Gtk.Widget] = None) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Setup UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Initialize state
        self._initialize_state()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        # Add CSS classes for styling
        self.add_css_class("example-widget")
        
        # Create child widgets
        label = Gtk.Label(label="Example")
        self.append(label)
    
    def _connect_signals(self) -> None:
        """Connect widget signals."""
        # Connect to relevant signals
        pass
    
    def _initialize_state(self) -> None:
        """Initialize widget state."""
        # Set initial values
        pass
```

## 🔧 Configuration

### Configuration Management
- **`config.py`** - Defines configuration dataclass
- **`config_manager.py`** - Handles loading/saving configuration
- **Location**: `~/.config/system-companion/config.json`

### Logging
- **Main log**: `~/.local/share/system-companion/logs/app.log`
- **Error log**: `~/.local/share/system-companion/logs/errors.log`
- **Performance log**: `~/.local/share/system-companion/logs/performance.log`

### Log Levels
- **DEBUG** - Detailed debugging information
- **INFO** - General information messages
- **WARNING** - Warning messages
- **ERROR** - Error messages

## 🎨 UI Development

### CSS Styling
- **File**: `resources/css/style.css`
- **Classes**: Use semantic class names (e.g., `dashboard-card`, `status-pill`)
- **Themes**: Support both light and dark themes

### Widget Guidelines
- Use `Gtk.Box` for layout containers
- Use `Gtk.Grid` for complex layouts
- Use `Adw.ViewStack` for tabbed interfaces
- Implement proper spacing and padding

### Common Patterns
```python
# Card layout
card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
card.add_css_class("dashboard-card")

# Status indicators
status_label = Gtk.Label(label="OK")
status_label.add_css_class("status-pill")
status_label.add_css_class("status-ok")

# Settings grid
grid = Gtk.Grid()
grid.add_css_class("settings-grid")
grid.set_row_spacing(12)
grid.set_column_spacing(16)
```

## 🔍 Debugging

### Debug Mode
Enable debug mode in Settings → Advanced Settings to see detailed logging.

### Common Issues
1. **GTK4 Import Errors**: Ensure all GTK4 development libraries are installed
2. **Permission Errors**: Some operations require root privileges (use `pkexec`)
3. **UI Not Updating**: Use `GLib.idle_add()` for UI updates from background threads

### Performance Profiling
```python
from system_companion.utils.logger import PerformanceTimer

with PerformanceTimer("operation_name"):
    # Your code here
    pass
```

## 📦 Building

### Development Build
```bash
meson setup build
cd build
ninja
```

### Flatpak Build (Future)
```bash
flatpak-builder build-dir packaging/flatpak/org.systemcompanion.app.yml
```

## 🤝 Contributing

### Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

### Commit Messages
Use conventional commit format:
```
feat: add new dashboard widget
fix: resolve memory leak in system monitor
docs: update installation instructions
style: format code according to PEP 8
```

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation is updated
- [ ] No performance regressions
- [ ] Error handling is implemented
- [ ] UI follows HIG guidelines

## 🔗 Resources

- [GTK4 Documentation](https://docs.gtk.org/gtk4/)
- [libadwaita Documentation](https://gnome.pages.gitlab.gnome.org/libadwaita/)
- [Python PyGObject](https://pygobject.readthedocs.io/)
- [GNOME Human Interface Guidelines](https://developer.gnome.org/hig/)
- [Meson Build System](https://mesonbuild.com/)

---

For more detailed documentation, see the [Documentation Index](README.md). 