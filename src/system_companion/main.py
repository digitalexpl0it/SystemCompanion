#!/usr/bin/env python3
"""
System Companion - Main application entry point.

This module initializes the GTK4 application and handles the main event loop.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio

from system_companion.ui.main_window import MainWindow
from system_companion.utils.logger import setup_logging, update_log_level
from system_companion.utils.config_manager import ConfigManager
from system_companion.data.database import Database


class SystemCompanionApp(Adw.Application):
    """Main application class for System Companion."""
    
    def __init__(self) -> None:
        super().__init__(
            application_id="dev.systemcompanion.app",
            flags=0
        )
        
        # Initialize configuration first
        self.config_manager = ConfigManager()
        
        # Get configuration
        config = self.config_manager.get_config()
        
        # Setup logging with config settings
        log_level = getattr(logging, config.get('log_level', 'INFO').upper(), logging.INFO)
        self.logger = setup_logging(level=log_level)
        
        # Initialize database
        self.database = Database()
        
        # Main window reference
        self.main_window: Optional[MainWindow] = None
        
        self.logger.info("System Companion application initialized")
    
    def do_activate(self) -> None:
        """Called when the application is activated."""
        try:
            # Create main window if it doesn't exist
            if not self.main_window:
                self.main_window = MainWindow(self)
                self.main_window.present()
            else:
                # Bring existing window to front
                self.main_window.present()
                
            self.logger.info("Application activated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to activate application: {e}")
            self._show_error_dialog("Failed to start System Companion", str(e))
    
    def do_startup(self) -> None:
        """Called when the application starts up."""
        try:
            # Call parent startup
            Adw.Application.do_startup(self)

            # Load custom CSS stylesheet
            import gi
            gi.require_version('Gdk', '4.0')
            from gi.repository import Gtk, Gdk
            css_provider = Gtk.CssProvider()
            css_provider.load_from_path("resources/css/style.css")
            display = Gdk.Display.get_default()
            Gtk.StyleContext.add_provider_for_display(
                display,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            
            # Initialize database
            self.database.initialize()
            
            # Setup application actions
            self._setup_actions()
            
            self.logger.info("Application startup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to startup application: {e}")
            raise
    
    def _setup_actions(self) -> None:
        """Setup application actions and shortcuts."""
        # Quit action
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self._on_quit_action)
        self.add_action(quit_action)
        
        # About action
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about_action)
        self.add_action(about_action)
        
        # Preferences action
        prefs_action = Gio.SimpleAction.new("preferences", None)
        prefs_action.connect("activate", self._on_preferences_action)
        self.add_action(prefs_action)
    
    def _on_quit_action(self, action: Gio.SimpleAction, param: GLib.Variant) -> None:
        """Handle quit action."""
        self.quit()
    
    def _on_about_action(self, action: Gio.SimpleAction, param: GLib.Variant) -> None:
        """Handle about action."""
        # TODO: Implement about dialog
        pass
    
    def _on_preferences_action(self, action: Gio.SimpleAction, param: GLib.Variant) -> None:
        """Handle preferences action."""
        # TODO: Implement preferences dialog
        pass
    
    def _show_error_dialog(self, title: str, message: str) -> None:
        """Show an error dialog to the user."""
        dialog = Adw.MessageDialog(
            transient_for=self.main_window,
            heading=title,
            body=message,
        )
        dialog.add_response("ok", "OK")
        dialog.present()


def main() -> int:
    """Main entry point for System Companion."""
    try:
        # Create and run application
        app = SystemCompanionApp()
        return app.run(sys.argv)
        
    except Exception as e:
        # Fallback error handling
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 