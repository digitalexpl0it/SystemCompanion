"""
Maintenance widget for System Companion.

This module provides the maintenance widget that displays
system maintenance tasks, cleanup opportunities, and task management.
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio

from ...core.maintenance_manager import MaintenanceManager, MaintenanceTask, TaskStatus, TaskPriority
from ...utils.exceptions import MaintenanceError


class MaintenanceWidget(Gtk.Box):
    """Maintenance widget displaying system maintenance tasks and cleanup."""
    
    def __init__(self, system_monitor) -> None:
        """Initialize the maintenance widget."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        self.logger = logging.getLogger("system_companion.ui.maintenance_widget")
        self.system_monitor = system_monitor
        self.maintenance_manager = MaintenanceManager()
        
        # Setup UI
        self._setup_ui()
        self._setup_update_timer()
        
        self.logger.info("Maintenance widget initialized")
    
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
        
        # Cleanup opportunities
        cleanup_section = self._create_cleanup_section()
        content_box.append(cleanup_section)
        
        # Maintenance tasks
        tasks_section = self._create_tasks_section()
        content_box.append(tasks_section)
        
        # Task history
        history_section = self._create_history_section()
        content_box.append(history_section)
        
        scrolled_window.set_child(content_box)
        self.append(scrolled_window)
    
    def _create_header(self) -> Gtk.Box:
        """Create the maintenance header."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.add_css_class("maintenance-header")
        
        # Title
        title_label = Gtk.Label(label="System Maintenance")
        title_label.add_css_class("title-1")
        header_box.append(title_label)

        # Spacer to push button to the right
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header_box.append(spacer)

        # Auto cleanup button
        self.auto_cleanup_button = Gtk.Button(label="Run Auto Cleanup")
        self.auto_cleanup_button.add_css_class("suggested-action")
        self.auto_cleanup_button.add_css_class("compact-button")
        self.auto_cleanup_button.set_size_request(120, 24)  # Set specific width and height
        self.auto_cleanup_button.connect("clicked", self._on_auto_cleanup)
        header_box.append(self.auto_cleanup_button)
        
        return header_box
    
    def _create_cleanup_section(self) -> Gtk.Box:
        """Create the cleanup opportunities section."""
        cleanup_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        cleanup_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="Cleanup Opportunities")
        title_label.add_css_class("title-2")
        cleanup_box.append(title_label)
        
        # Cleanup info grid
        self.cleanup_grid = Gtk.Grid()
        self.cleanup_grid.set_row_spacing(8)
        self.cleanup_grid.set_column_spacing(16)
        
        # Package cache
        pkg_cache_label = Gtk.Label(label="Package Cache:")
        pkg_cache_label.set_xalign(0)
        self.cleanup_grid.attach(pkg_cache_label, 0, 0, 1, 1)
        
        self.pkg_cache_value_label = Gtk.Label(label="Loading...")
        self.cleanup_grid.attach(self.pkg_cache_value_label, 1, 0, 1, 1)
        
        # Temp files
        temp_files_label = Gtk.Label(label="Temporary Files:")
        temp_files_label.set_xalign(0)
        self.cleanup_grid.attach(temp_files_label, 0, 1, 1, 1)
        
        self.temp_files_value_label = Gtk.Label(label="Loading...")
        self.cleanup_grid.attach(self.temp_files_value_label, 1, 1, 1, 1)
        
        # Log files
        log_files_label = Gtk.Label(label="Log Files:")
        log_files_label.set_xalign(0)
        self.cleanup_grid.attach(log_files_label, 0, 2, 1, 1)
        
        self.log_files_value_label = Gtk.Label(label="Loading...")
        self.cleanup_grid.attach(self.log_files_value_label, 1, 2, 1, 1)
        
        # Browser cache
        browser_cache_label = Gtk.Label(label="Browser Cache:")
        browser_cache_label.set_xalign(0)
        self.cleanup_grid.attach(browser_cache_label, 0, 3, 1, 1)
        
        self.browser_cache_value_label = Gtk.Label(label="Loading...")
        self.cleanup_grid.attach(self.browser_cache_value_label, 1, 3, 1, 1)
        
        # Total cleanup
        total_label = Gtk.Label(label="Total Cleanup:")
        total_label.set_xalign(0)
        total_label.add_css_class("title-3")
        self.cleanup_grid.attach(total_label, 0, 4, 1, 1)
        
        self.total_cleanup_value_label = Gtk.Label(label="Loading...")
        self.total_cleanup_value_label.add_css_class("title-3")
        self.cleanup_grid.attach(self.total_cleanup_value_label, 1, 4, 1, 1)
        
        cleanup_box.append(self.cleanup_grid)
        
        return cleanup_box
    
    def _create_tasks_section(self) -> Gtk.Box:
        """Create the maintenance tasks section with two columns."""
        tasks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        tasks_box.add_css_class("dashboard-card")

        # Title
        title_label = Gtk.Label(label="Maintenance Tasks")
        title_label.add_css_class("title-2")
        tasks_box.append(title_label)

        # Tasks grid (2 columns)
        self.tasks_grid = Gtk.Grid()
        self.tasks_grid.set_column_spacing(12)
        self.tasks_grid.set_row_spacing(8)
        self.tasks_grid.set_margin_top(4)
        self.tasks_grid.set_margin_bottom(4)
        self.tasks_grid.set_hexpand(True)
        self.tasks_grid.set_vexpand(False)
        tasks_box.append(self.tasks_grid)

        return tasks_box
    
    def _create_history_section(self) -> Gtk.Box:
        """Create the task history section."""
        history_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        history_box.add_css_class("dashboard-card")
        
        # Title row with clear button
        title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title_label = Gtk.Label(label="Task History")
        title_label.add_css_class("title-2")
        title_row.append(title_label)
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        title_row.append(spacer)
        clear_button = Gtk.Button(label="Clear History")
        clear_button.add_css_class("destructive-action")
        clear_button.add_css_class("compact-button")
        clear_button.set_margin_start(8)
        clear_button.set_margin_end(8)
        clear_button.set_margin_top(2)
        clear_button.set_margin_bottom(2)
        clear_button.set_tooltip_text("Clear all task history")
        clear_button.set_size_request(90, 24)  # Increased width for longer text
        clear_button.connect("clicked", self._on_clear_task_history)
        title_row.append(clear_button)
        history_box.append(title_row)
        
        # History list
        self.history_listbox = Gtk.ListBox()
        self.history_listbox.add_css_class("history-list")
        history_box.append(self.history_listbox)
        
        return history_box

    def _on_clear_task_history(self, button: Gtk.Button) -> None:
        """Clear the task history in manager and UI."""
        try:
            self.maintenance_manager.clear_task_history()
            self._update_task_history()
            self._show_notification("Task History Cleared", "All maintenance task history has been cleared.")
        except Exception as e:
            self.logger.error(f"Failed to clear task history: {e}")
            self._show_notification("Error", f"Failed to clear task history: {e}")
    
    def _setup_update_timer(self) -> None:
        """Setup the update timer for maintenance monitoring."""
        # Update immediately
        self._update_maintenance_info()
        
        # Set up timer for periodic updates (every 60 seconds)
        GLib.timeout_add_seconds(60, self._update_maintenance_info)
    
    def _update_maintenance_info(self) -> bool:
        """Update maintenance information and return True to continue the timer."""
        try:
            # Update cleanup opportunities
            self._update_cleanup_info()
            
            # Update maintenance tasks
            self._update_maintenance_tasks()
            
            # Update task history
            self._update_task_history()
            
            return True  # Continue the timer
            
        except Exception as e:
            self.logger.error(f"Failed to update maintenance info: {e}")
            return True  # Continue the timer even on error
    
    def _update_cleanup_info(self) -> None:
        """Update cleanup opportunities information."""
        try:
            cleanup_info = self.maintenance_manager.get_system_cleanup_info()
            
            # Update package cache
            pkg_cache_size = cleanup_info.get('package_cache_size', 0)
            self.pkg_cache_value_label.set_label(self._format_size(pkg_cache_size))
            
            # Update temp files
            temp_files_size = cleanup_info.get('temp_files_size', 0)
            self.temp_files_value_label.set_label(self._format_size(temp_files_size))
            
            # Update log files
            log_files_size = cleanup_info.get('log_files_size', 0)
            self.log_files_value_label.set_label(self._format_size(log_files_size))
            
            # Update browser cache
            browser_cache_size = cleanup_info.get('browser_cache_size', 0)
            self.browser_cache_value_label.set_label(self._format_size(browser_cache_size))
            
            # Update total cleanup
            total_cleanup = cleanup_info.get('total_cleanup_size', 0)
            self.total_cleanup_value_label.set_label(self._format_size(total_cleanup))
            
        except Exception as e:
            self.logger.error(f"Failed to update cleanup info: {e}")
    
    def _update_maintenance_tasks(self) -> None:
        """Update maintenance tasks list for two-column layout."""
        try:
            # Always scan for storage devices before updating cards
            self.maintenance_manager.scan_storage_devices()
            # Clear existing tasks
            child = self.tasks_grid.get_first_child()
            while child is not None:
                next_child = child.get_next_sibling()
                self.tasks_grid.remove(child)
                child = next_child

            # Get all tasks
            tasks = self.maintenance_manager.get_all_tasks()
            filtered_tasks = []
            for task in tasks:
                if task.id == 'check_disk_health' and not self.maintenance_manager.has_sata():
                    continue
                if task.id == 'check_nvme_health' and not self.maintenance_manager.has_nvme():
                    continue
                filtered_tasks.append(task)

            # Distribute tasks into two columns
            col_count = 2
            for idx, task in enumerate(filtered_tasks):
                # Create task row (same as before)
                task_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                task_box.add_css_class("task-card")
                task_box.set_margin_start(4)
                task_box.set_margin_end(4)
                task_box.set_margin_top(4)
                task_box.set_margin_bottom(4)
                task_box.set_spacing(2)

                # Task header using Gtk.Box for background
                header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                header_box.add_css_class("task-card-header")
                name_label = Gtk.Label(label=task.name)
                name_label.add_css_class("title-4")
                name_label.set_xalign(0)
                name_label.set_hexpand(True)
                header_box.append(name_label)
                task_box.append(header_box)

                # Priority pill
                priority_label = Gtk.Label(label=task.priority.value.capitalize())
                priority_label.add_css_class("pill")
                priority_label.add_css_class(f"pill-{task.priority.value}")
                priority_label.set_margin_start(8)
                header_box.append(priority_label)

                # Status pill
                status_label = Gtk.Label(label=task.status.value.capitalize())
                status_label.add_css_class("pill")
                status_label.add_css_class(f"pill-{task.status.value}")
                status_label.set_margin_start(8)
                header_box.append(status_label)

                # Description
                desc_label = Gtk.Label(label=task.description)
                desc_label.set_xalign(0)
                desc_label.set_wrap(True)
                desc_label.set_max_width_chars(50)
                desc_label.set_hexpand(False)
                task_box.append(desc_label)

                # Persistent warning for check_disk_health if smartctl is not installed
                if task.id == 'check_disk_health' and self.maintenance_manager.is_smartctl_not_found():
                    warning_label = Gtk.Label(label="smartctl is not installed. Install it with: sudo apt install smartmontools")
                    warning_label.set_xalign(0)
                    warning_label.set_wrap(True)
                    warning_label.set_hexpand(False)
                    warning_label.set_margin_top(2)
                    warning_label.set_margin_bottom(2)
                    warning_label.set_markup('<span foreground="red" weight="bold">smartctl is not installed. Install it with: sudo apt install smartmontools</span>')
                    task_box.append(warning_label)
                # Persistent warning for check_disk_health if no SMART devices found
                if task.id == 'check_disk_health' and self.maintenance_manager.no_smart_devices():
                    warning_label = Gtk.Label(label="No supported disks found for SMART health check.")
                    warning_label.set_xalign(0)
                    warning_label.set_wrap(True)
                    warning_label.set_hexpand(False)
                    warning_label.set_margin_top(2)
                    warning_label.set_margin_bottom(2)
                    warning_label.set_markup('<span foreground="red" weight="bold">No supported disks found for SMART health check.</span>')
                    task_box.append(warning_label)

                # Persistent warning for firmware update task if no supported hardware
                if task.id == 'update_firmware' and self.maintenance_manager.has_no_supported_firmware_devices():
                    warning_label = Gtk.Label(label="No supported hardware for firmware updates detected")
                    warning_label.set_xalign(0)
                    warning_label.set_wrap(True)
                    warning_label.set_hexpand(False)
                    warning_label.set_margin_top(2)
                    warning_label.set_margin_bottom(2)
                    warning_label.set_markup('<span foreground="red" weight="bold">No supported hardware for firmware updates detected</span>')
                    task_box.append(warning_label)

                # Task details
                details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                details_box.set_spacing(1)
                category_label = Gtk.Label(label=f"Category: {task.category}")
                category_label.add_css_class("caption")
                category_label.set_wrap(True)
                category_label.set_max_width_chars(30)
                category_label.set_hexpand(False)
                details_box.append(category_label)
                duration_label = Gtk.Label(label=f"Duration: {task.estimated_duration}")
                duration_label.add_css_class("caption")
                duration_label.set_wrap(True)
                duration_label.set_max_width_chars(20)
                duration_label.set_hexpand(False)
                details_box.append(duration_label)
                if task.last_run:
                    last_run_str = task.last_run.strftime("%Y-%m-%d %H:%M")
                    last_run_label = Gtk.Label(label=f"Last Run: {last_run_str}")
                    last_run_label.add_css_class("caption")
                    last_run_label.set_wrap(True)
                    last_run_label.set_max_width_chars(25)
                    last_run_label.set_hexpand(False)
                    details_box.append(last_run_label)
                task_box.append(details_box)

                # Spacer to push the button to the bottom
                spacer = Gtk.Box()
                spacer.set_vexpand(True)
                task_box.append(spacer)

                # Run button
                run_button = Gtk.Button(label="Run Task")
                run_button.add_css_class("suggested-action")
                run_button.connect("clicked", self._on_run_task, task.id)
                
                # Disable button if no supported hardware for firmware updates
                if task.id == 'update_firmware' and self.maintenance_manager.has_no_supported_firmware_devices():
                    run_button.set_sensitive(False)
                    run_button.set_tooltip_text("No supported hardware detected for firmware updates")
                
                # Disable button if smartctl is not available for disk health check
                if task.id == 'check_disk_health' and self.maintenance_manager.is_smartctl_not_found():
                    run_button.set_sensitive(False)
                    run_button.set_tooltip_text("smartctl is not installed. Install with: sudo apt install smartmontools")
                
                # Disable button if no SMART devices found for disk health check
                if task.id == 'check_disk_health' and self.maintenance_manager.no_smart_devices():
                    run_button.set_sensitive(False)
                    run_button.set_tooltip_text("No supported disks found for SMART health check")
                
                task_box.append(run_button)

                # Add to grid directly (no frame wrapper)
                row = idx // col_count
                col = idx % col_count
                self.tasks_grid.attach(task_box, col, row, 1, 1)

        except Exception as e:
            self.logger.error(f"Failed to update maintenance tasks: {e}")
    
    def _update_task_history(self) -> None:
        """Update task history list."""
        try:
            # Clear existing history
            while self.history_listbox.get_first_child():
                self.history_listbox.remove(self.history_listbox.get_first_child())
            
            # Get recent task history
            history = self.maintenance_manager.get_task_history(limit=10)
            
            for result in history:
                # Create history row
                row = Gtk.ListBoxRow()
                
                # History content
                history_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                history_box.set_margin_start(8)
                history_box.set_margin_end(8)
                history_box.set_margin_top(4)
                history_box.set_margin_bottom(4)
                history_box.set_spacing(12)
                
                # Task ID
                task_id_label = Gtk.Label(label=result.task_id)
                task_id_label.set_xalign(0)
                task_id_label.set_hexpand(True)
                history_box.append(task_id_label)
                
                # Success status
                status_label = Gtk.Label(label="✓" if result.success else "✗")
                status_label.add_css_class("success" if result.success else "error")
                history_box.append(status_label)
                
                # Duration
                duration_label = Gtk.Label(label=f"{result.duration:.1f}s")
                history_box.append(duration_label)
                
                # Timestamp
                timestamp_str = result.timestamp.strftime("%Y-%m-%d %H:%M")
                timestamp_label = Gtk.Label(label=timestamp_str)
                history_box.append(timestamp_label)
                
                row.set_child(history_box)
                self.history_listbox.append(row)
            
        except Exception as e:
            self.logger.error(f"Failed to update task history: {e}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable format."""
        try:
            if size_bytes == 0:
                return "0 B"
            
            size_names = ["B", "KB", "MB", "GB", "TB"]
            i = 0
            while size_bytes >= 1024 and i < len(size_names) - 1:
                size_bytes /= 1024.0
                i += 1
            
            return f"{size_bytes:.1f} {size_names[i]}"
            
        except Exception:
            return "0 B"
    
    def _on_auto_cleanup(self, button: Gtk.Button) -> None:
        """Handle auto cleanup button click."""
        try:
            # Disable button during cleanup
            button.set_sensitive(False)
            button.set_label("Running Cleanup...")
            
            # Run automated cleanup in background
            def run_cleanup():
                try:
                    results = self.maintenance_manager.run_automated_cleanup()
                    
                    # Update UI in main thread
                    GLib.idle_add(self._cleanup_completed, results)
                    
                except Exception as e:
                    self.logger.error(f"Auto cleanup failed: {e}")
                    GLib.idle_add(self._cleanup_failed, str(e))
            
            # Start cleanup thread
            import threading
            thread = threading.Thread(target=run_cleanup)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to start auto cleanup: {e}")
            button.set_sensitive(True)
            button.set_label("Run Auto Cleanup")
    
    def _cleanup_completed(self, results) -> None:
        """Handle cleanup completion."""
        try:
            # Re-enable button
            self.auto_cleanup_button.set_sensitive(True)
            self.auto_cleanup_button.set_label("Run Auto Cleanup")
            
            # Update maintenance info
            self._update_maintenance_info()
            
            # Show completion message
            success_count = len([r for r in results if r.success])
            total_count = len(results)
            self._show_notification("Auto Cleanup Completed", f"{success_count}/{total_count} tasks completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to handle cleanup completion: {e}")
    
    def _cleanup_failed(self, error_message: str) -> None:
        """Handle cleanup failure."""
        try:
            # Re-enable button
            self.auto_cleanup_button.set_sensitive(True)
            self.auto_cleanup_button.set_label("Run Auto Cleanup")
            
            # Show error message
            self._show_notification("Auto Cleanup Failed", error_message)
            
        except Exception as e:
            self.logger.error(f"Failed to handle cleanup failure: {e}")
    
    def _on_run_task(self, button: Gtk.Button, task_id: str) -> None:
        """Handle run task button click."""
        try:
            # Disable button during task execution
            button.set_sensitive(False)
            button.set_label("Running...")
            
            # Run task in background
            def run_task():
                try:
                    result = self.maintenance_manager.run_task(task_id)
                    
                    # Update UI in main thread
                    GLib.idle_add(self._task_completed, result)
                    
                except Exception as e:
                    self.logger.error(f"Task execution failed: {e}")
                    GLib.idle_add(self._task_failed, str(e))
            
            # Start task thread
            import threading
            thread = threading.Thread(target=run_task)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to start task: {e}")
            button.set_sensitive(True)
            button.set_label("Run Task")
    
    def _task_completed(self, result) -> None:
        """Handle task completion."""
        try:
            # Update maintenance info
            self._update_maintenance_info()
            
            # Show completion message
            status = "Success" if result.success else "Failed"
            self._show_notification(f"Task {result.task_id}", f"Task completed with status: {status}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle task completion: {e}")
    
    def _task_failed(self, error_message: str) -> None:
        """Handle task failure."""
        try:
            # Update maintenance info to refresh UI (e.g., firmware warning)
            self._update_maintenance_info()
            # Show error message
            self._show_notification("Task Failed", error_message)
            
        except Exception as e:
            self.logger.error(f"Failed to handle task failure: {e}")
    
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
        self.logger.info("Cleaning up maintenance widget")
        # Any cleanup code would go here 