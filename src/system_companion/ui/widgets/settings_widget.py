"""
Settings widget for System Companion.

This module provides the settings widget that displays
application settings, preferences, and configuration options.
"""

import logging
from typing import Optional, Dict, Any
import json
import os
import subprocess
import shutil
import sys

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio

from ...utils.config_manager import ConfigManager


class SettingsWidget(Gtk.Box):
    """Settings widget displaying application settings and preferences."""
    
    def __init__(self, main_window=None) -> None:
        """Initialize the settings widget."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        self.logger = logging.getLogger("system_companion.ui.settings_widget")
        self.config_manager = ConfigManager()
        self.main_window = main_window
        
        # Setup UI
        self._setup_ui()
        self._load_settings()
        
        self.logger.info("Settings widget initialized")
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        # Main container with scrolling
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        
        # Main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_margin_start(16)
        content_box.set_margin_end(16)
        content_box.set_margin_top(16)
        content_box.set_margin_bottom(16)
        content_box.set_spacing(16)
        
        # Header
        header = self._create_header()
        content_box.append(header)
        
        # General settings
        general_section = self._create_general_section()
        content_box.append(general_section)
        

        

        
        # Notification settings
        notification_section = self._create_notification_section()
        content_box.append(notification_section)
        
        # Advanced settings
        advanced_section = self._create_advanced_section()
        content_box.append(advanced_section)
        
        # Action buttons
        action_buttons = self._create_action_buttons()
        content_box.append(action_buttons)
        
        scrolled_window.set_child(content_box)
        self.append(scrolled_window)
    
    def _create_header(self) -> Gtk.Box:
        """Create the settings header."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.add_css_class("settings-header")
        
        # Title
        title_label = Gtk.Label(label="Application Settings")
        title_label.add_css_class("title-1")
        header_box.append(title_label)
        
        return header_box
    
    def _create_general_section(self) -> Gtk.Box:
        """Create the general settings section."""
        general_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        general_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="General Settings")
        title_label.add_css_class("title-2")
        general_box.append(title_label)
        
        # Settings grid
        general_grid = Gtk.Grid()
        general_grid.add_css_class("settings-grid")
        general_grid.set_row_spacing(12)
        general_grid.set_column_spacing(16)
        
        # Auto-start application
        autostart_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        autostart_box.set_spacing(8)
        
        autostart_label = Gtk.Label(label="Start on Boot:")
        autostart_label.set_xalign(0)
        autostart_label.set_hexpand(True)
        autostart_box.append(autostart_label)
        
        self.autostart_switch = Gtk.Switch()
        self.autostart_switch.connect("state-set", self._on_autostart_changed)
        autostart_box.append(self.autostart_switch)
        
        general_grid.attach(autostart_box, 0, 0, 1, 1)
        

        
        general_box.append(general_grid)
        
        return general_box
    

    

    
    def _create_notification_section(self) -> Gtk.Box:
        """Create the notification settings section."""
        notification_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        notification_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="Notification Settings")
        title_label.add_css_class("title-2")
        notification_box.append(title_label)
        
        # Settings grid
        notification_grid = Gtk.Grid()
        notification_grid.add_css_class("settings-grid")
        notification_grid.set_row_spacing(12)
        notification_grid.set_column_spacing(16)
        
        # Enable notifications
        enable_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        enable_box.set_spacing(8)
        
        enable_label = Gtk.Label(label="Enable Notifications:")
        enable_label.set_xalign(0)
        enable_label.set_hexpand(True)
        enable_box.append(enable_label)
        
        self.notifications_switch = Gtk.Switch()
        self.notifications_switch.connect("state-set", self._on_notifications_changed)
        enable_box.append(self.notifications_switch)
        
        notification_grid.attach(enable_box, 0, 0, 1, 1)
        
        # Critical alerts
        critical_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        critical_box.set_spacing(8)
        
        critical_label = Gtk.Label(label="Critical Alerts:")
        critical_label.set_xalign(0)
        critical_label.set_hexpand(True)
        critical_box.append(critical_label)
        
        self.critical_switch = Gtk.Switch()
        self.critical_switch.connect("state-set", self._on_critical_changed)
        critical_box.append(self.critical_switch)
        
        notification_grid.attach(critical_box, 0, 1, 1, 1)
        
        # Performance alerts
        perf_alert_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        perf_alert_box.set_spacing(8)
        
        perf_alert_label = Gtk.Label(label="Performance Alerts:")
        perf_alert_label.set_xalign(0)
        perf_alert_label.set_hexpand(True)
        perf_alert_box.append(perf_alert_label)
        
        self.perf_alert_switch = Gtk.Switch()
        self.perf_alert_switch.connect("state-set", self._on_perf_alert_changed)
        perf_alert_box.append(self.perf_alert_switch)
        
        notification_grid.attach(perf_alert_box, 0, 2, 1, 1)
        
        # Security alerts
        security_alert_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        security_alert_box.set_spacing(8)
        
        security_alert_label = Gtk.Label(label="Security Alerts:")
        security_alert_label.set_xalign(0)
        security_alert_label.set_hexpand(True)
        security_alert_box.append(security_alert_label)
        
        self.security_alert_switch = Gtk.Switch()
        self.security_alert_switch.connect("state-set", self._on_security_alert_changed)
        security_alert_box.append(self.security_alert_switch)
        
        notification_grid.attach(security_alert_box, 0, 3, 1, 1)
        
        notification_box.append(notification_grid)
        
        return notification_box
    
    def _create_advanced_section(self) -> Gtk.Box:
        """Create the advanced settings section."""
        advanced_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        advanced_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="Advanced Settings")
        title_label.add_css_class("title-2")
        advanced_box.append(title_label)
        
        # Settings grid
        advanced_grid = Gtk.Grid()
        advanced_grid.add_css_class("settings-grid")
        advanced_grid.set_row_spacing(12)
        advanced_grid.set_column_spacing(16)
        
        # Debug mode
        debug_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        debug_box.set_spacing(8)
        
        debug_label = Gtk.Label(label="Debug Mode:")
        debug_label.set_xalign(0)
        debug_label.set_hexpand(True)
        debug_box.append(debug_label)
        
        self.debug_switch = Gtk.Switch()
        self.debug_switch.connect("state-set", self._on_debug_changed)
        debug_box.append(self.debug_switch)
        
        advanced_grid.attach(debug_box, 0, 0, 1, 1)
        
        # Log level
        log_label = Gtk.Label(label="Log Level:")
        log_label.set_xalign(0)
        advanced_grid.attach(log_label, 0, 1, 1, 1)
        
        self.log_combo = Gtk.ComboBoxText()
        self.log_combo.append("DEBUG", "Debug")
        self.log_combo.append("INFO", "Info")
        self.log_combo.append("WARNING", "Warning")
        self.log_combo.append("ERROR", "Error")
        self.log_combo.set_active_id("INFO")
        self.log_combo.connect("changed", self._on_log_level_changed)
        advanced_grid.attach(self.log_combo, 1, 1, 1, 1)
        
        # Data retention (days)
        retention_label = Gtk.Label(label="Data Retention (days):")
        retention_label.set_xalign(0)
        advanced_grid.attach(retention_label, 0, 2, 1, 1)
        
        self.retention_spinbutton = Gtk.SpinButton()
        self.retention_spinbutton.set_range(1, 365)
        self.retention_spinbutton.set_increments(1, 7)
        self.retention_spinbutton.set_value(30)
        self.retention_spinbutton.connect("value-changed", self._on_retention_changed)
        advanced_grid.attach(self.retention_spinbutton, 1, 2, 1, 1)
        
        # View logs button
        logs_button = Gtk.Button(label="View Log Files")
        logs_button.connect("clicked", self._on_view_logs)
        logs_button.add_css_class("compact-button")
        advanced_grid.attach(logs_button, 0, 3, 2, 1)
        
        advanced_box.append(advanced_grid)
        
        return advanced_box
    
    def _create_action_buttons(self) -> Gtk.Box:
        """Create action buttons."""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.add_css_class("settings-actions")
        button_box.set_spacing(12)
        
        # Reset to defaults
        reset_button = Gtk.Button(label="Reset to Defaults")
        reset_button.connect("clicked", self._on_reset_defaults)
        button_box.append(reset_button)
        
        # Save settings
        save_button = Gtk.Button(label="Save Settings")
        save_button.add_css_class("suggested-action")
        save_button.connect("clicked", self._on_save_settings)
        button_box.append(save_button)
        
        return button_box
    
    def _load_settings(self) -> None:
        """Load current settings from configuration."""
        try:
            config = self.config_manager.get_config()
            
            # General settings - check actual autostart status
            autostart_enabled = self._is_autostart_enabled()
            self.autostart_switch.set_active(autostart_enabled)
            
            # Notification settings
            self.notifications_switch.set_active(config.get('notifications_enabled', True))
            self.critical_switch.set_active(config.get('critical_notifications', True))
            self.perf_alert_switch.set_active(config.get('performance_notifications', True))
            self.security_alert_switch.set_active(config.get('security_notifications', True))
            
            # Advanced settings
            self.debug_switch.set_active(config.get('debug_mode', False))
            
            log_level = config.get('log_level', 'INFO')
            self.log_combo.set_active_id(log_level)
            
            self.retention_spinbutton.set_value(config.get('data_retention_days', 30))
            
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
    
    def _save_settings(self) -> None:
        """Save current settings to configuration."""
        try:
            config = {
                # General settings
                'autostart': self.autostart_switch.get_active(),
                
                # Notification settings
                'notifications_enabled': self.notifications_switch.get_active(),
                'critical_notifications': self.critical_switch.get_active(),
                'performance_notifications': self.perf_alert_switch.get_active(),
                'security_notifications': self.security_alert_switch.get_active(),
                
                # Advanced settings
                'debug_mode': self.debug_switch.get_active(),
                'log_level': self.log_combo.get_active_id(),
                'data_retention_days': int(self.retention_spinbutton.get_value())
            }
            
            self.config_manager.update_config(config)
            self.config_manager.save_config()
            
            self.logger.info("Settings saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
    
    # Event handlers for settings changes
    def _on_autostart_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle autostart setting change."""
        try:
            if state:
                self._enable_autostart()
            else:
                self._disable_autostart()
            
            self.logger.info(f"Autostart setting changed: {state}")
            
        except Exception as e:
            self.logger.error(f"Failed to change autostart setting: {e}")
            self._show_notification("Error", f"Failed to update autostart setting: {e}")
            # Revert the switch state
            switch.set_state(not state)
    
    def _enable_autostart(self) -> None:
        """Enable application autostart."""
        try:
            # Create autostart directory if it doesn't exist
            autostart_dir = os.path.expanduser("~/.config/autostart")
            os.makedirs(autostart_dir, exist_ok=True)
            
            # Create desktop entry
            desktop_entry = f"""[Desktop Entry]
Type=Application
Name=System Companion
Comment=System monitoring and maintenance tool
Exec={sys.executable} {os.path.abspath(__file__)}
Icon=system-companion
Terminal=false
Categories=System;Utility;
"""
            
            desktop_file = os.path.join(autostart_dir, "system-companion.desktop")
            with open(desktop_file, 'w') as f:
                f.write(desktop_entry)
            
            # Make it executable
            os.chmod(desktop_file, 0o755)
            
        except Exception as e:
            raise Exception(f"Failed to enable autostart: {e}")
    
    def _disable_autostart(self) -> None:
        """Disable application autostart."""
        try:
            desktop_file = os.path.expanduser("~/.config/autostart/system-companion.desktop")
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
                
        except Exception as e:
            raise Exception(f"Failed to disable autostart: {e}")
    
    def _is_autostart_enabled(self) -> bool:
        """Check if autostart is currently enabled."""
        try:
            desktop_file = os.path.expanduser("~/.config/autostart/system-companion.desktop")
            return os.path.exists(desktop_file)
        except Exception as e:
            self.logger.error(f"Failed to check autostart status: {e}")
            return False
    

    

    

    

    
    def _on_notifications_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle notifications setting change."""
        self.logger.debug(f"Notifications setting changed: {state}")
    
    def _on_critical_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle critical notifications setting change."""
        self.logger.debug(f"Critical notifications setting changed: {state}")
    
    def _on_perf_alert_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle performance alerts setting change."""
        self.logger.debug(f"Performance alerts setting changed: {state}")
    
    def _on_security_alert_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle security alerts setting change."""
        self.logger.debug(f"Security alerts setting changed: {state}")
    
    def _on_debug_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle debug mode setting change."""
        from ...utils.logger import update_log_level
        
        # Update log level immediately
        if state:
            # Enable debug logging
            update_log_level('DEBUG')
            self.logger.info("Debug mode enabled")
        else:
            # Revert to configured log level
            config = self.config_manager.get_config()
            log_level = config.get('log_level', 'INFO')
            update_log_level(log_level)
            self.logger.info("Debug mode disabled")
    
    def _on_log_level_changed(self, combo: Gtk.ComboBoxText) -> None:
        """Handle log level setting change."""
        from ...utils.logger import update_log_level
        
        level = combo.get_active_id()
        update_log_level(level)
        self.logger.info(f"Log level changed to: {level}")
    
    def _on_retention_changed(self, spinbutton: Gtk.SpinButton) -> None:
        """Handle data retention setting change."""
        days = int(spinbutton.get_value())
        self.logger.info(f"Data retention changed to: {days} days")
        
        # TODO: Implement data cleanup based on retention days
        # This would involve cleaning up old database records
    
    def _on_view_logs(self, button: Gtk.Button) -> None:
        """Handle view logs button click."""
        try:
            from ...utils.logger import get_log_file_path
            import subprocess
            import os
            
            log_file = get_log_file_path()
            
            if not log_file.exists():
                self._show_notification("No Logs", "No log files found yet.")
                return
            
            # Try to open the log file with the default text editor
            try:
                subprocess.Popen(['xdg-open', str(log_file)])
                self.logger.info(f"Opened log file: {log_file}")
            except FileNotFoundError:
                # Fallback to gedit if xdg-open is not available
                try:
                    subprocess.Popen(['gedit', str(log_file)])
                    self.logger.info(f"Opened log file with gedit: {log_file}")
                except FileNotFoundError:
                    self._show_notification("No Editor", "Could not find a text editor to open log files.")
                    
        except Exception as e:
            self.logger.error(f"Failed to open log files: {e}")
            self._show_notification("Error", f"Failed to open log files: {e}")
    
    def _on_reset_defaults(self, button: Gtk.Button) -> None:
        """Handle reset to defaults button click."""
        try:
            # Create confirmation dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.get_root(),
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Reset Settings",
                secondary_text="Are you sure you want to reset all settings to their default values? This action cannot be undone."
            )
            
            dialog.connect("response", self._on_reset_confirmation)
            dialog.present()
            
        except Exception as e:
            self.logger.error(f"Failed to show reset confirmation: {e}")
    
    def _on_reset_confirmation(self, dialog: Gtk.MessageDialog, response: int) -> None:
        """Handle reset confirmation dialog response."""
        try:
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                # Reset to default values
                self._reset_to_defaults()
                self._show_notification("Settings Reset", "All settings have been reset to their default values.")
            
        except Exception as e:
            self.logger.error(f"Failed to handle reset confirmation: {e}")
    
    def _reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        try:
            # General settings
            self.autostart_switch.set_active(False)
            
            # Notification settings
            self.notifications_switch.set_active(True)
            self.critical_switch.set_active(True)
            self.perf_alert_switch.set_active(True)
            self.security_alert_switch.set_active(True)
            
            # Advanced settings
            self.debug_switch.set_active(False)
            self.log_combo.set_active_id("INFO")
            self.retention_spinbutton.set_value(30)
            
        except Exception as e:
            self.logger.error(f"Failed to reset settings: {e}")
    
    def _on_save_settings(self, button: Gtk.Button) -> None:
        """Handle save settings button click."""
        try:
            # Save settings
            self._save_settings()
            
            # Show success message
            self._show_notification("Settings Saved", "Your settings have been saved successfully.")
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            self._show_notification("Save Failed", f"Failed to save settings: {e}")
    
    def _show_notification(self, title: str, message: str) -> None:
        """Show a notification message."""
        try:
            # Create a simple notification dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.get_root(),
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=title,
                secondary_text=message
            )
            
            dialog.connect("response", lambda dialog, response: dialog.destroy())
            dialog.present()
            
        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")
    
    def cleanup(self) -> None:
        """Clean up resources when the widget is destroyed."""
        self.logger.info("Cleaning up settings widget")
        # Any cleanup code would go here 