"""
Main window for System Companion.

This module provides the main application window with sidebar navigation
and content area for different system monitoring views.
"""

import logging
from typing import Optional

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

from .widgets.dashboard_widget import DashboardWidget
from .widgets.performance_widget import PerformanceWidget


class MainWindow(Gtk.ApplicationWindow):
    """Main application window."""
    
    def __init__(self, application: Adw.Application) -> None:
        """Initialize the main window."""
        super().__init__(application=application)
        
        self.logger = logging.getLogger("system_companion.ui.main_window")
        self.application = application
        
        # Current view tracking
        self.current_view = "dashboard"
        self.view_widgets = {}
        

        
        # Setup window
        self._setup_window()
        
        # Setup UI
        self._setup_ui()
        
        self.logger.info("Main window initialized")
    
    def _setup_window(self) -> None:
        """Setup window properties."""
        self.set_title("System Companion")
        self.set_default_size(1200, 800)
        self.set_resizable(True)
        
        # Add CSS classes
        self.add_css_class("main-window")
        
        # Setup titlebar
        self._setup_titlebar()
    
    def _setup_titlebar(self) -> None:
        """Setup the window titlebar."""
        # Use default window titlebar instead of custom header bar
        # This ensures the window title is properly displayed
        self.set_decorated(True)
        self.set_resizable(True)
        self.set_modal(False)
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.add_css_class("main-container")
        
        # Sidebar - create this first (left side)
        sidebar = self._create_sidebar()
        main_box.append(sidebar)
        
        # Content area - create this second (right side)
        self.content_area = self._create_content_area()
        main_box.append(self.content_area)
        
        # Set the main widget
        self.set_child(main_box)
        
        # Initialize with dashboard view
        self._show_view("dashboard")
        
        # Now select the dashboard row in navigation
        first_row = self.nav_listbox.get_row_at_index(0)
        if first_row:
            self.nav_listbox.select_row(first_row)
    
    def _create_sidebar(self) -> Gtk.Box:
        """Create the sidebar navigation."""
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar.add_css_class("sidebar")
        sidebar.set_size_request(250, -1)
        
        # App title
        title_label = Gtk.Label(label="System Companion")
        title_label.add_css_class("title-1")
        title_label.add_css_class("app-title")
        title_label.set_margin_start(16)
        title_label.set_margin_end(16)
        title_label.set_margin_top(16)
        title_label.set_margin_bottom(16)
        sidebar.append(title_label)
        
        # Navigation list
        self.nav_listbox = Gtk.ListBox()
        self.nav_listbox.add_css_class("navigation-list")
        self.nav_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.nav_listbox.connect("row-selected", self._on_navigation_changed)
        
        # Navigation items
        nav_items = [
            ("dashboard", "Dashboard", "system-monitor-symbolic"),
            ("health", "System Health", "health-symbolic"),
            ("performance", "Performance", "speedometer-symbolic"),
            ("maintenance", "Maintenance", "wrench-symbolic"),
            ("security", "Security", "shield-symbolic"),
            ("settings", "Settings", "preferences-system-symbolic")
        ]
        
        for item_id, item_name, icon_name in nav_items:
            row = self._create_nav_row(item_id, item_name, icon_name)
            self.nav_listbox.append(row)
        
        sidebar.append(self.nav_listbox)
        
        # Don't select dashboard here - it will be selected after content_area is created
        # first_row = self.nav_listbox.get_row_at_index(0)
        # if first_row:
        #     self.nav_listbox.select_row(first_row)
        
        return sidebar
    
    def _create_nav_row(self, item_id: str, item_name: str, icon_name: str) -> Gtk.ListBoxRow:
        """Create a navigation row."""
        row = Gtk.ListBoxRow()
        row.set_name(f"nav-{item_id}")
        
        # Row content
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_spacing(12)
        
        # Icon (placeholder - we'll use text for now)
        icon_label = Gtk.Label(label="●")
        icon_label.add_css_class("nav-icon")
        box.append(icon_label)
        
        # Label
        label = Gtk.Label(label=item_name)
        label.set_xalign(0)
        label.set_hexpand(True)
        box.append(label)
        
        row.set_child(box)
        return row
    
    def _create_content_area(self) -> Gtk.Box:
        """Create the main content area."""
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.add_css_class("content-area")
        
        return content
    
    def _on_navigation_changed(self, listbox: Gtk.ListBox, row: Optional[Gtk.ListBoxRow]) -> None:
        """Handle navigation selection changes."""
        if not row:
            return
        
        # Get the view ID from the row name
        row_name = row.get_name()
        if row_name.startswith("nav-"):
            view_id = row_name[4:]  # Remove "nav-" prefix
            self._show_view(view_id)
    
    def _show_view(self, view_id: str) -> None:
        """Show the specified view."""
        try:
            # Clear current content
            while self.content_area.get_first_child():
                self.content_area.remove(self.content_area.get_first_child())
            
            # Get or create the view widget
            if view_id not in self.view_widgets:
                self.view_widgets[view_id] = self._create_view_widget(view_id)
            
            # Show the view
            view_widget = self.view_widgets[view_id]
            self.content_area.append(view_widget)
            
            # Update titlebar
            self._update_titlebar(view_id)
            
            # Update current view
            self.current_view = view_id
            
        except Exception as e:
            self.logger.error(f"Failed to show view '{view_id}': {e}")
            # Show error message
            error_label = Gtk.Label(label=f"Failed to load {view_id} view")
            error_label.add_css_class("title-2")
            self.content_area.append(error_label)
    
    def _create_view_widget(self, view_id: str):
        """Create a widget for the specified view."""
        if view_id == "dashboard":
            return DashboardWidget()
        elif view_id == "performance":
            # Create performance widget with system monitor
            from .widgets.performance_widget import PerformanceWidget
            # We need to get the system monitor from the dashboard widget
            dashboard_widget = self.view_widgets.get("dashboard")
            if dashboard_widget and hasattr(dashboard_widget, 'system_monitor'):
                return PerformanceWidget(dashboard_widget.system_monitor)
            else:
                # Fallback to placeholder if system monitor not available
                return self._create_placeholder_widget("Performance Analysis", "Performance analysis features coming soon...")
        elif view_id == "health":
            # Create health widget with system monitor
            from .widgets.health_widget import HealthWidget
            dashboard_widget = self.view_widgets.get("dashboard")
            if dashboard_widget and hasattr(dashboard_widget, 'system_monitor'):
                return HealthWidget(dashboard_widget.system_monitor)
            else:
                return self._create_placeholder_widget("System Health", "System health monitoring features coming soon...")
        elif view_id == "maintenance":
            # Create maintenance widget with system monitor
            from .widgets.maintenance_widget import MaintenanceWidget
            dashboard_widget = self.view_widgets.get("dashboard")
            if dashboard_widget and hasattr(dashboard_widget, 'system_monitor'):
                return MaintenanceWidget(dashboard_widget.system_monitor)
            else:
                return self._create_placeholder_widget("Maintenance", "System maintenance features coming soon...")
        elif view_id == "security":
            # Create security widget with system monitor
            from .widgets.security_widget import SecurityWidget
            dashboard_widget = self.view_widgets.get("dashboard")
            if dashboard_widget and hasattr(dashboard_widget, 'system_monitor'):
                return SecurityWidget(dashboard_widget.system_monitor)
            else:
                return self._create_placeholder_widget("Security", "Security monitoring features coming soon...")
        elif view_id == "settings":
            # Create settings widget
            from .widgets.settings_widget import SettingsWidget
            return SettingsWidget(self)
        else:
            return self._create_placeholder_widget("Unknown View", f"View '{view_id}' not implemented yet.")
    
    def _create_placeholder_widget(self, title: str, message: str) -> Gtk.Box:
        """Create a placeholder widget for unimplemented views."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_spacing(16)
        
        # Title
        title_label = Gtk.Label(label=title)
        title_label.add_css_class("title-1")
        title_label.set_justify(Gtk.Justification.CENTER)
        box.append(title_label)
        
        # Message
        message_label = Gtk.Label(label=message)
        message_label.add_css_class("title-2")
        message_label.set_justify(Gtk.Justification.CENTER)
        message_label.set_margin_top(50)
        box.append(message_label)
        
        return box
    
    def _update_titlebar(self, view_id: str) -> None:
        """Update the titlebar with the current view name."""
        # Convert view_id to display name
        view_names = {
            "dashboard": "Dashboard",
            "health": "System Health",
            "performance": "Performance",
            "maintenance": "Maintenance",
            "security": "Security",
            "settings": "Settings"
        }
        display_name = view_names.get(view_id, view_id.title())
        
        # Update the window title
        window_title = f"System Companion - {display_name}"
        self.set_title(window_title)
    

    
    def cleanup(self) -> None:
        """Clean up resources when the window is destroyed."""
        self.logger.info("Cleaning up main window")
        
        # Clean up view widgets
        for widget in self.view_widgets.values():
            if hasattr(widget, 'cleanup'):
                widget.cleanup() 