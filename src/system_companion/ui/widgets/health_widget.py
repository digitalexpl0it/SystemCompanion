"""
System Health widget for System Companion.

This module provides the system health widget that displays
comprehensive health monitoring, alerts, and diagnostics.
"""

import logging
import time
import subprocess
from typing import Optional, List, Dict
from datetime import datetime, timedelta

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

from ...core.system_monitor import SystemMonitor
from ...core.performance_analyzer import PerformanceAnalyzer
from ...utils.exceptions import MonitoringError


class HealthAlert:
    """Represents a health alert."""
    def __init__(self, severity: str, title: str, message: str, component: str, timestamp: datetime):
        self.severity = severity
        self.title = title
        self.message = message
        self.component = component
        self.timestamp = timestamp


class HealthWidget(Gtk.Box):
    """System health widget displaying comprehensive health monitoring."""
    
    def __init__(self, system_monitor: SystemMonitor) -> None:
        """Initialize the health widget."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        self.logger = logging.getLogger("system_companion.ui.health_widget")
        self.system_monitor = system_monitor
        self.performance_analyzer = PerformanceAnalyzer(system_monitor)
        
        # Health alerts
        self.health_alerts = []
        
        # Setup UI
        self._setup_ui()
        self._setup_update_timer()
        
        self.logger.info("Health widget initialized")
    
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
        
        # Overall health status
        health_status = self._create_health_status()
        content_box.append(health_status)
        
        # Health alerts
        alerts_section = self._create_alerts_section()
        content_box.append(alerts_section)
        
        # Component health and battery health (side by side)
        health_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        health_row.set_spacing(16)
        
        # Component health
        component_health = self._create_component_health()
        component_health.set_hexpand(True)
        health_row.append(component_health)
        
        # Battery health (if available)
        battery_section = self._create_battery_section()
        if battery_section:
            battery_section.set_hexpand(True)
            health_row.append(battery_section)
        
        content_box.append(health_row)
        
        # System information and hardware info (side by side)
        info_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        info_row.set_spacing(16)
        
        # System information
        system_info_section = self._create_diagnostics_section()
        system_info_section.set_hexpand(True)
        info_row.append(system_info_section)
        
        # Hardware information
        hardware_section = self._create_hardware_section()
        hardware_section.set_hexpand(True)
        info_row.append(hardware_section)
        
        content_box.append(info_row)
        
        # System services health
        services_section = self._create_services_section()
        content_box.append(services_section)
        
        # Security monitoring
        security_section = self._create_security_section()
        content_box.append(security_section)
        
        # System logs monitoring
        logs_section = self._create_logs_section()
        content_box.append(logs_section)
        
        scrolled_window.set_child(content_box)
        self.append(scrolled_window)
    
    def _create_header(self) -> Gtk.Box:
        """Create the health header."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.add_css_class("health-header")
        header_box.set_hexpand(True)
        
        # Title
        title_label = Gtk.Label(label="System Health Monitor")
        title_label.add_css_class("title-2")
        title_label.set_xalign(0)
        header_box.append(title_label)
        
        # Refresh button
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header_box.append(spacer)
        self.refresh_button = Gtk.Button(label="Refresh")
        self.refresh_button.add_css_class("suggested-action")
        self.refresh_button.set_hexpand(False)
        self.refresh_button.connect("clicked", self._on_refresh)
        header_box.append(self.refresh_button)
        
        return header_box
    
    def _create_health_status(self) -> Gtk.Box:
        """Create the overall health status section."""
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        status_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="Overall System Health")
        title_label.add_css_class("title-2")
        status_box.append(title_label)
        
        # Health score
        self.health_score_label = Gtk.Label(label="Health Score: Loading...")
        self.health_score_label.add_css_class("title-3")
        status_box.append(self.health_score_label)
        
        # Health bar
        self.health_bar = Gtk.ProgressBar()
        self.health_bar.set_show_text(True)
        self.health_bar.set_fraction(0.0)
        status_box.append(self.health_bar)
        
        # Status grid
        status_grid = Gtk.Grid()
        status_grid.set_row_spacing(8)
        status_grid.set_column_spacing(16)
        
        # Uptime
        uptime_label = Gtk.Label(label="System Uptime:")
        uptime_label.set_xalign(0)
        status_grid.attach(uptime_label, 0, 0, 1, 1)
        
        self.uptime_value_label = Gtk.Label(label="Loading...")
        status_grid.attach(self.uptime_value_label, 1, 0, 1, 1)
        
        # Last boot
        boot_label = Gtk.Label(label="Last Boot:")
        boot_label.set_xalign(0)
        status_grid.attach(boot_label, 0, 1, 1, 1)
        
        self.boot_value_label = Gtk.Label(label="Loading...")
        status_grid.attach(self.boot_value_label, 1, 1, 1, 1)
        
        # Kernel version
        kernel_label = Gtk.Label(label="Kernel Version:")
        kernel_label.set_xalign(0)
        status_grid.attach(kernel_label, 0, 2, 1, 1)
        
        self.kernel_value_label = Gtk.Label(label="Loading...")
        status_grid.attach(self.kernel_value_label, 1, 2, 1, 1)
        
        status_box.append(status_grid)
        
        return status_box
    
    def _create_alerts_section(self) -> Gtk.Box:
        """Create the health alerts section."""
        alerts_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        alerts_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="Health Alerts")
        title_label.add_css_class("title-2")
        alerts_box.append(title_label)
        
        # Alerts list
        self.alerts_listbox = Gtk.ListBox()
        self.alerts_listbox.add_css_class("alerts-list")
        alerts_box.append(self.alerts_listbox)
        
        # No alerts message
        self.no_alerts_label = Gtk.Label(label="No health alerts detected")
        self.no_alerts_label.add_css_class("caption")
        self.no_alerts_label.add_css_class("dim-label")
        alerts_box.append(self.no_alerts_label)
        
        return alerts_box
    
    def _create_component_health(self) -> Gtk.Box:
        """Create the component health section."""
        component_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        component_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="Component Health")
        title_label.add_css_class("title-2")
        component_box.append(title_label)
        
        # Component grid
        self.component_grid = Gtk.Grid()
        self.component_grid.set_row_spacing(12)
        self.component_grid.set_column_spacing(16)
        
        component_box.append(self.component_grid)
        
        return component_box
    
    def _create_diagnostics_section(self) -> Gtk.Box:
        """Create the system diagnostics section."""
        diagnostics_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        diagnostics_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="System Information")
        title_label.add_css_class("title-2")
        diagnostics_box.append(title_label)
        
        # Diagnostics list
        self.diagnostics_listbox = Gtk.ListBox()
        self.diagnostics_listbox.add_css_class("diagnostics-list")
        diagnostics_box.append(self.diagnostics_listbox)
        
        return diagnostics_box
    
    def _create_hardware_section(self) -> Gtk.Box:
        """Create the hardware information section."""
        hardware_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hardware_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="Hardware Information")
        title_label.add_css_class("title-2")
        hardware_box.append(title_label)
        
        # Hardware info grid
        self.hardware_grid = Gtk.Grid()
        self.hardware_grid.set_row_spacing(8)
        self.hardware_grid.set_column_spacing(16)
        
        hardware_box.append(self.hardware_grid)
        
        return hardware_box
    
    def _create_services_section(self) -> Gtk.Box:
        """Create the system services health section."""
        services_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        services_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="System Services Health")
        title_label.add_css_class("title-2")
        services_box.append(title_label)
        
        # Services list
        self.services_listbox = Gtk.ListBox()
        self.services_listbox.add_css_class("services-list")
        services_box.append(self.services_listbox)
        
        # No issues message
        self.no_service_issues_label = Gtk.Label(label="All critical services are running")
        self.no_service_issues_label.add_css_class("caption")
        self.no_service_issues_label.add_css_class("dim-label")
        services_box.append(self.no_service_issues_label)
        
        return services_box
    
    def _create_security_section(self) -> Gtk.Box:
        """Create the security monitoring section."""
        security_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        security_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="Security Status")
        title_label.add_css_class("title-2")
        security_box.append(title_label)
        
        # Security grid
        self.security_grid = Gtk.Grid()
        self.security_grid.set_row_spacing(12)
        self.security_grid.set_column_spacing(16)
        
        security_box.append(self.security_grid)
        
        return security_box
    
    def _create_battery_section(self) -> Optional[Gtk.Box]:
        """Create the battery health section (if battery is available)."""
        try:
            import psutil
            
            # Check if battery exists
            battery = psutil.sensors_battery()
            if not battery:
                return None  # No battery, don't show section
            
            battery_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            battery_box.add_css_class("dashboard-card")
            
            # Title
            title_label = Gtk.Label(label="Battery Health")
            title_label.add_css_class("title-2")
            battery_box.append(title_label)
            
            # Battery info grid
            self.battery_grid = Gtk.Grid()
            self.battery_grid.set_row_spacing(8)
            self.battery_grid.set_column_spacing(16)
            
            battery_box.append(self.battery_grid)
            
            return battery_box
            
        except Exception as e:
            self.logger.error(f"Failed to create battery section: {e}")
            return None
    
    def _create_logs_section(self) -> Gtk.Box:
        """Create the system logs monitoring section."""
        logs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        logs_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="System Logs")
        title_label.add_css_class("title-2")
        logs_box.append(title_label)
        
        # Logs list with scrolling
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_min_content_height(200)
        scrolled_window.set_max_content_height(400)
        
        self.logs_listbox = Gtk.ListBox()
        self.logs_listbox.add_css_class("logs-list")
        scrolled_window.set_child(self.logs_listbox)
        logs_box.append(scrolled_window)
        
        # No issues message
        self.no_log_issues_label = Gtk.Label(label="No recent errors or warnings detected")
        self.no_log_issues_label.add_css_class("caption")
        self.no_log_issues_label.add_css_class("dim-label")
        logs_box.append(self.no_log_issues_label)
        
        return logs_box
    
    def _setup_update_timer(self) -> None:
        """Setup the update timer for health monitoring."""
        # Update immediately
        self._update_health_status()
        
        # Set up timer for periodic updates (every 30 seconds)
        GLib.timeout_add_seconds(30, self._update_health_status)
    
    def _update_health_status(self) -> bool:
        """Update health status and return True to continue the timer."""
        try:
            # Update overall health
            self._update_overall_health()
            
            # Update component health
            self._update_component_health()
            
            # Update health alerts
            self._update_health_alerts()
            
            # Update system diagnostics
            self._update_system_diagnostics()
            
            # Update hardware information
            self._update_hardware_information()
            
            # Update system services
            self._update_system_services()
            
            # Update security status
            self._update_security_status()
            
            # Update battery health
            self._update_battery_health()
            
            # Update system logs
            self._update_system_logs()
            
            return True  # Continue the timer
            
        except Exception as e:
            self.logger.error(f"Failed to update health status: {e}")
            return True  # Continue the timer even on error
    
    def _update_overall_health(self) -> None:
        """Update the overall health status."""
        try:
            # Get health score
            health_score = self.system_monitor.get_system_health_score()
            
            # Update health score label
            if health_score >= 80:
                status = "Excellent"
                css_class = "health-excellent"
            elif health_score >= 60:
                status = "Good"
                css_class = "health-good"
            elif health_score >= 40:
                status = "Fair"
                css_class = "health-fair"
            else:
                status = "Poor"
                css_class = "health-poor"
            
            self.health_score_label.set_label(f"Health Score: {status} ({health_score:.0f}/100)")
            
            # Update progress bar
            self.health_bar.set_fraction(health_score / 100.0)
            
            # Update CSS class
            self.health_score_label.remove_css_class("health-excellent")
            self.health_score_label.remove_css_class("health-good")
            self.health_score_label.remove_css_class("health-fair")
            self.health_score_label.remove_css_class("health-poor")
            self.health_score_label.add_css_class(css_class)
            
            # Update system info
            self._update_system_info()
            
        except Exception as e:
            self.logger.error(f"Failed to update overall health: {e}")
    
    def _update_system_info(self) -> None:
        """Update system information."""
        try:
            import psutil
            import platform
            
            # Uptime
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_days = int(uptime_seconds // 86400)
            uptime_hours = int((uptime_seconds % 86400) // 3600)
            uptime_minutes = int((uptime_seconds % 3600) // 60)
            
            if uptime_days > 0:
                uptime_str = f"{uptime_days}d {uptime_hours}h {uptime_minutes}m"
            elif uptime_hours > 0:
                uptime_str = f"{uptime_hours}h {uptime_minutes}m"
            else:
                uptime_str = f"{uptime_minutes}m"
            
            self.uptime_value_label.set_label(uptime_str)
            
            # Last boot
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            boot_str = boot_time.strftime("%Y-%m-%d %H:%M")
            self.boot_value_label.set_label(boot_str)
            
            # Kernel version
            kernel_version = platform.release()
            self.kernel_value_label.set_label(kernel_version)
            
        except Exception as e:
            self.logger.error(f"Failed to update system info: {e}")
    
    def _update_component_health(self) -> None:
        """Update component health status."""
        try:
            # Clear existing components
            while self.component_grid.get_first_child():
                self.component_grid.remove(self.component_grid.get_first_child())
            
            # Get component health data
            components = self._get_component_health_data()
            
            # Add component rows
            for i, (component, data) in enumerate(components.items()):
                # Component name
                name_label = Gtk.Label(label=component)
                name_label.set_xalign(0)
                self.component_grid.attach(name_label, 0, i, 1, 1)
                
                # Status indicator
                status_label = Gtk.Label(label=data['status'])
                status_label.add_css_class("pill")
                status_label.add_css_class(f"pill-{data['status'].lower()}")
                self.component_grid.attach(status_label, 1, i, 1, 1)
                
                # Details
                details_label = Gtk.Label(label=data['details'])
                details_label.set_xalign(0)
                self.component_grid.attach(details_label, 2, i, 1, 1)
            
        except Exception as e:
            self.logger.error(f"Failed to update component health: {e}")
    
    def _get_component_health_data(self) -> Dict[str, Dict]:
        """Get component health data."""
        try:
            components = {}
            
            # CPU health
            cpu_info = self.system_monitor.get_cpu_info()
            if cpu_info.usage_percent > 90:
                cpu_status = "critical"
                cpu_details = f"High usage: {cpu_info.usage_percent:.1f}%"
            elif cpu_info.usage_percent > 80:
                cpu_status = "warning"
                cpu_details = f"Elevated usage: {cpu_info.usage_percent:.1f}%"
            else:
                cpu_status = "OK"
                cpu_details = f"Normal: {cpu_info.usage_percent:.1f}%"
            
            if cpu_info.temperature_celsius and cpu_info.temperature_celsius > 80:
                cpu_status = "critical"
                cpu_details += f", High temp: {cpu_info.temperature_celsius:.1f}°C"
            
            components['CPU'] = {
                'status': cpu_status,
                'details': cpu_details
            }
            
            # Memory health
            memory_info = self.system_monitor.get_memory_info()
            if memory_info.usage_percent > 90:
                mem_status = "critical"
                mem_details = f"High usage: {memory_info.usage_percent:.1f}%"
            elif memory_info.usage_percent > 80:
                mem_status = "warning"
                mem_details = f"Elevated usage: {memory_info.usage_percent:.1f}%"
            else:
                mem_status = "OK"
                mem_details = f"Normal: {memory_info.usage_percent:.1f}%"
            
            if memory_info.swap_usage_percent > 50:
                mem_status = "warning"
                mem_details += f", High swap: {memory_info.swap_usage_percent:.1f}%"
            
            components['Memory'] = {
                'status': mem_status,
                'details': mem_details
            }
            
            # Disk health
            disk_info_list = self.system_monitor.get_disk_info()
            if disk_info_list:
                disk_info = disk_info_list[0]  # Primary disk
                if disk_info.usage_percent > 95:
                    disk_status = "critical"
                    disk_details = f"Critical usage: {disk_info.usage_percent:.1f}%"
                elif disk_info.usage_percent > 90:
                    disk_status = "warning"
                    disk_details = f"High usage: {disk_info.usage_percent:.1f}%"
                else:
                    disk_status = "OK"
                    disk_details = f"Normal: {disk_info.usage_percent:.1f}%"
                
                components['Storage'] = {
                    'status': disk_status,
                    'details': disk_details
                }
            
            # Network health
            network_info_list = self.system_monitor.get_network_info()
            if network_info_list:
                network_status = "OK"
                network_details = f"{len(network_info_list)} interfaces active"
                
                # Check for high network usage
                for net_info in network_info_list:
                    if net_info.speed_mbps and net_info.speed_mbps > 100:
                        network_status = "warning"
                        network_details = f"High activity: {net_info.speed_mbps:.1f} Mbps"
                        break
                
                components['Network'] = {
                    'status': network_status,
                    'details': network_details
                }
            
            return components
            
        except Exception as e:
            self.logger.error(f"Failed to get component health data: {e}")
            return {}
    
    def _update_health_alerts(self) -> None:
        """Update health alerts."""
        try:
            # Clear existing alerts
            while self.alerts_listbox.get_first_child():
                self.alerts_listbox.remove(self.alerts_listbox.get_first_child())
            
            # Get performance issues as health alerts
            issues = self.performance_analyzer.analyze_system_performance()
            
            if not issues:
                # Show no alerts message
                self.no_alerts_label.set_visible(True)
                return
            
            # Hide no alerts message
            self.no_alerts_label.set_visible(False)
            
            for issue in issues:
                # Create alert row
                row = Gtk.ListBoxRow()
                
                # Alert content
                alert_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                alert_box.set_margin_start(8)
                alert_box.set_margin_end(8)
                alert_box.set_margin_top(8)
                alert_box.set_margin_bottom(8)
                alert_box.set_spacing(4)
                
                # Alert header
                header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                
                # Title
                title_label = Gtk.Label(label=issue.title)
                title_label.add_css_class("title-4")
                title_label.set_xalign(0)
                title_label.set_hexpand(True)
                header_box.append(title_label)
                
                # Severity badge
                severity_label = Gtk.Label(label=issue.severity.value.upper())
                severity_label.add_css_class("pill")
                severity_label.add_css_class(f"pill-{issue.severity.value}")
                header_box.append(severity_label)
                
                alert_box.append(header_box)
                
                # Description
                desc_label = Gtk.Label(label=issue.description)
                desc_label.set_xalign(0)
                desc_label.set_wrap(True)
                alert_box.append(desc_label)
                
                # Recommendation
                rec_label = Gtk.Label(label=f"Recommendation: {issue.recommendation}")
                rec_label.add_css_class("caption")
                rec_label.set_xalign(0)
                rec_label.set_wrap(True)
                alert_box.append(rec_label)
                
                row.set_child(alert_box)
                self.alerts_listbox.append(row)
            
        except Exception as e:
            self.logger.error(f"Failed to update health alerts: {e}")
    
    def _update_system_diagnostics(self) -> None:
        """Update system diagnostics."""
        try:
            # Clear existing diagnostics
            while self.diagnostics_listbox.get_first_child():
                self.diagnostics_listbox.remove(self.diagnostics_listbox.get_first_child())
            
            # Get diagnostic information
            diagnostics = self._get_system_diagnostics()
            
            for diagnostic in diagnostics:
                # Create diagnostic row
                row = Gtk.ListBoxRow()
                
                # Diagnostic content
                diag_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                diag_box.set_margin_start(8)
                diag_box.set_margin_end(8)
                diag_box.set_margin_top(4)
                diag_box.set_margin_bottom(4)
                diag_box.set_spacing(12)
                
                # Diagnostic name
                name_label = Gtk.Label(label=diagnostic['name'])
                name_label.set_xalign(0)
                name_label.set_hexpand(True)
                diag_box.append(name_label)
                
                # Diagnostic value
                value_label = Gtk.Label(label=diagnostic['value'])
                diag_box.append(value_label)
                
                # Status indicator
                status_label = Gtk.Label(label="●")
                status_label.add_css_class(f"status-{diagnostic['status']}")
                diag_box.append(status_label)
                
                row.set_child(diag_box)
                self.diagnostics_listbox.append(row)
            
        except Exception as e:
            self.logger.error(f"Failed to update system diagnostics: {e}")
    
    def _get_system_diagnostics(self) -> List[Dict]:
        """Get system diagnostic information."""
        try:
            import psutil
            import platform
            
            diagnostics = []
            
            # System load
            load_avg = psutil.getloadavg()
            load_str = f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}"
            load_status = "OK" if load_avg[0] < 1.0 else "warning"
            diagnostics.append({
                'name': 'System Load (1m, 5m, 15m)',
                'value': load_str,
                'status': load_status
            })
            
            # CPU cores
            cpu_cores = psutil.cpu_count()
            diagnostics.append({
                'name': 'CPU Cores',
                'value': str(cpu_cores),
                'status': 'OK'
            })
            
            # Memory total
            memory_total = psutil.virtual_memory().total / (1024**3)
            diagnostics.append({
                'name': 'Total Memory',
                'value': f"{memory_total:.1f} GB",
                'status': 'OK'
            })
            
            # Disk space
            disk_usage = psutil.disk_usage('/')
            disk_total = disk_usage.total / (1024**3)
            diagnostics.append({
                'name': 'Total Disk Space',
                'value': f"{disk_total:.1f} GB",
                'status': 'OK'
            })
            
            # Network interfaces
            network_interfaces = len(psutil.net_if_addrs())
            diagnostics.append({
                'name': 'Network Interfaces',
                'value': str(network_interfaces),
                'status': 'OK'
            })
            
            # Operating system
            os_name = platform.system()
            os_version = platform.release()
            
            # Get Ubuntu version
            ubuntu_version = "Unknown"
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME='):
                            ubuntu_version = line.split('=', 1)[1].strip().strip('"')
                            break
            except:
                pass
            
            diagnostics.append({
                'name': 'Operating System',
                'value': f"{os_name} {os_version}",
                'status': 'OK'
            })
            
            diagnostics.append({
                'name': 'Ubuntu Version',
                'value': ubuntu_version,
                'status': 'OK'
            })
            
            return diagnostics
            
        except Exception as e:
            self.logger.error(f"Failed to get system diagnostics: {e}")
            return []
    
    def _on_refresh(self, button: Gtk.Button) -> None:
        """Handle refresh button click."""
        try:
            # Disable button during refresh
            button.set_sensitive(False)
            button.set_label("Refreshing...")
            
            # Update health status
            self._update_health_status()
            
            # Re-enable button
            button.set_sensitive(True)
            button.set_label("Refresh")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh health status: {e}")
            button.set_sensitive(True)
            button.set_label("Refresh")
    
    def _update_system_services(self) -> None:
        """Update system services health status."""
        try:
            # Clear existing services
            while self.services_listbox.get_first_child():
                self.services_listbox.remove(self.services_listbox.get_first_child())
            
            # Get critical services status
            services = self._get_critical_services_status()
            
            # Always show services, but hide no issues message if we have services
            if services:
                self.no_service_issues_label.set_visible(False)
            else:
                self.no_service_issues_label.set_visible(True)
                return
            
            for service in services:
                # Create service row
                row = Gtk.ListBoxRow()
                
                # Service content
                service_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                service_box.set_margin_start(8)
                service_box.set_margin_end(8)
                service_box.set_margin_top(4)
                service_box.set_margin_bottom(4)
                service_box.set_spacing(12)
                
                # Service name
                name_label = Gtk.Label(label=service['name'])
                name_label.set_xalign(0)
                name_label.set_hexpand(True)
                service_box.append(name_label)
                
                # Status badge
                status_label = Gtk.Label(label=service['status'].upper())
                status_label.add_css_class("pill")
                status_label.add_css_class(f"pill-{service['status']}")
                service_box.append(status_label)
                
                # Details
                details_label = Gtk.Label(label=service['details'])
                details_label.set_xalign(0)
                service_box.append(details_label)
                
                row.set_child(service_box)
                self.services_listbox.append(row)
            
        except Exception as e:
            self.logger.error(f"Failed to update system services: {e}")
    
    def _update_security_status(self) -> None:
        """Update security status monitoring."""
        try:
            # Clear existing security items
            while self.security_grid.get_first_child():
                self.security_grid.remove(self.security_grid.get_first_child())
            
            # Get security data
            security_data = self._get_security_data()
            
            # Add security rows
            for i, (item, data) in enumerate(security_data.items()):
                # Item name
                name_label = Gtk.Label(label=item)
                name_label.set_xalign(0)
                self.security_grid.attach(name_label, 0, i, 1, 1)
                
                # Status indicator
                status_label = Gtk.Label(label=data['status'])
                status_label.add_css_class("pill")
                status_label.add_css_class(f"pill-{data['status']}")
                self.security_grid.attach(status_label, 1, i, 1, 1)
                
                # Details
                details_label = Gtk.Label(label=data['details'])
                details_label.set_xalign(0)
                self.security_grid.attach(details_label, 2, i, 1, 1)
                
                # Action button (if applicable)
                if 'action' in data:
                    action_btn = Gtk.Button(label=data['action'])
                    action_btn.add_css_class("flat")
                    action_btn.add_css_class("suggested-action")
                    action_btn.connect("clicked", data['callback'])
                    self.security_grid.attach(action_btn, 3, i, 1, 1)
            
        except Exception as e:
            self.logger.error(f"Failed to update security status: {e}")
    
    def _update_battery_health(self) -> None:
        """Update battery health information."""
        try:
            if not hasattr(self, 'battery_grid'):
                return  # Battery section not created
            
            # Clear existing battery info
            while self.battery_grid.get_first_child():
                self.battery_grid.remove(self.battery_grid.get_first_child())
            
            # Get battery data
            battery_data = self._get_battery_data()
            
            if not battery_data:
                return  # No battery data
            
            # Add battery rows
            for i, (item, data) in enumerate(battery_data.items()):
                # Item name
                name_label = Gtk.Label(label=item)
                name_label.set_xalign(0)
                self.battery_grid.attach(name_label, 0, i, 1, 1)
                
                # Value
                value_label = Gtk.Label(label=data['value'])
                self.battery_grid.attach(value_label, 1, i, 1, 1)
                
                # Status indicator (if applicable)
                if 'status' in data:
                    status_label = Gtk.Label(label=data['status'])
                    status_label.add_css_class("pill")
                    status_label.add_css_class(f"pill-{data['status']}")
                    self.battery_grid.attach(status_label, 2, i, 1, 1)
            
        except Exception as e:
            self.logger.error(f"Failed to update battery health: {e}")
    
    def _update_system_logs(self) -> None:
        """Update system logs monitoring."""
        try:
            # Clear existing logs
            while self.logs_listbox.get_first_child():
                self.logs_listbox.remove(self.logs_listbox.get_first_child())
            
            # Get recent log entries
            log_entries = self._get_recent_log_entries()
            
            if not log_entries:
                # Show no issues message
                self.no_log_issues_label.set_visible(True)
                return
            
            # Hide no issues message
            self.no_log_issues_label.set_visible(False)
            
            for entry in log_entries:
                # Create log row
                row = Gtk.ListBoxRow()
                
                # Log content
                log_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                log_box.set_margin_start(8)
                log_box.set_margin_end(8)
                log_box.set_margin_top(4)
                log_box.set_margin_bottom(4)
                log_box.set_spacing(4)
                
                # Log header
                header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                
                # Timestamp
                time_label = Gtk.Label(label=entry['timestamp'])
                time_label.add_css_class("caption")
                time_label.set_xalign(0)
                time_label.set_hexpand(True)
                header_box.append(time_label)
                
                # Severity badge
                severity_label = Gtk.Label(label=entry['severity'].upper())
                severity_label.add_css_class("pill")
                severity_label.add_css_class(f"pill-{entry['severity']}")
                header_box.append(severity_label)
                
                log_box.append(header_box)
                
                # Message
                msg_label = Gtk.Label(label=entry['message'])
                msg_label.set_xalign(0)
                msg_label.set_wrap(True)
                log_box.append(msg_label)
                
                row.set_child(log_box)
                self.logs_listbox.append(row)
            
        except Exception as e:
            self.logger.error(f"Failed to update system logs: {e}")
    
    def _get_critical_services_status(self) -> List[Dict]:
        """Get status of critical system services."""
        try:
            import subprocess
            import json
            
            services = []
            
            # List of critical services to monitor (Ubuntu 24.04 specific)
            critical_services = [
                'systemd-networkd', 'systemd-resolved', 'systemd-timesyncd',
                'ssh', 'ufw', 'cron', 'rsyslog', 'NetworkManager'
            ]
            
            for service in critical_services:
                try:
                    # Check service status using systemctl
                    result = subprocess.run(
                        ['systemctl', 'is-active', service],
                        capture_output=True, text=True, timeout=5
                    )
                    
                    status = result.stdout.strip()
                    
                    # Determine status and details
                    if status == 'active':
                        service_status = 'OK'
                        details = 'Service is running'
                    elif status == 'inactive':
                        service_status = 'critical'
                        details = 'Service is inactive'
                    elif status == 'failed':
                        service_status = 'critical'
                        details = 'Service failed to start'
                    else:
                        service_status = 'warning'
                        details = f'Service status: {status}'
                    
                    services.append({
                        'name': service,
                        'status': service_status,
                        'details': details
                    })
                    
                except subprocess.TimeoutExpired:
                    services.append({
                        'name': service,
                        'status': 'warning',
                        'details': 'Status check timeout'
                    })
                except Exception:
                    # Service might not exist, skip
                    continue
            
            return services
            
        except Exception as e:
            self.logger.error(f"Failed to get services status: {e}")
            return []
    
    def _get_security_data(self) -> Dict[str, Dict]:
        """Get security monitoring data."""
        try:
            import subprocess
            import re
            
            security_data = {}
            
            # Check for failed login attempts
            try:
                result = subprocess.run(
                    ['journalctl', '-u', 'sshd', '--since', '1 hour ago', '-o', 'json'],
                    capture_output=True, text=True, timeout=10
                )
                
                failed_logins = 0
                for line in result.stdout.split('\n'):
                    if line.strip() and 'Failed password' in line:
                        failed_logins += 1
                
                if failed_logins > 0:
                    security_data['Failed Logins'] = {
                        'status': 'warning',
                        'details': f'{failed_logins} failed attempts in last hour',
                        'action': 'View List',
                        'callback': self._on_view_failed_logins
                    }
                else:
                    security_data['Failed Logins'] = {
                        'status': 'OK',
                        'details': 'No failed attempts detected'
                    }
                    
            except Exception as e:
                security_data['Failed Logins'] = {
                    'status': 'unknown',
                    'details': 'Unable to check login attempts'
                }
            
            # Check fail2ban status
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', 'fail2ban'],
                    capture_output=True, text=True, timeout=5
                )
                
                if result.stdout.strip() == 'active':
                    security_data['Fail2ban'] = {
                        'status': 'OK',
                        'details': 'Fail2ban is active and protecting SSH'
                    }
                else:
                    security_data['Fail2ban'] = {
                        'status': 'warning',
                        'details': 'Fail2ban is not installed or not running',
                        'action': 'Install',
                        'callback': self._on_install_fail2ban
                    }
                    
            except Exception:
                security_data['Fail2ban'] = {
                    'status': 'unknown',
                    'details': 'Unable to check fail2ban status',
                    'action': 'Install',
                    'callback': self._on_install_fail2ban
                }
            
            return security_data
            
        except Exception as e:
            self.logger.error(f"Failed to get security data: {e}")
            return {}
    
    def _get_battery_data(self) -> Dict[str, Dict]:
        """Get battery health data."""
        try:
            import psutil
            
            battery = psutil.sensors_battery()
            if not battery:
                return {}
            
            battery_data = {}
            
            # Battery percentage
            if battery.percent is not None:
                battery_data['Battery Level'] = {
                    'value': f"{battery.percent:.1f}%",
                    'status': 'OK' if battery.percent > 20 else 'warning'
                }
            
            # Power plugged
            if battery.power_plugged is not None:
                status = 'OK' if battery.power_plugged else 'warning'
                details = 'Plugged in' if battery.power_plugged else 'On battery'
                battery_data['Power Status'] = {
                    'value': details,
                    'status': status
                }
            
            # Time remaining (if available)
            if battery.secsleft != -1:
                hours = battery.secsleft // 3600
                minutes = (battery.secsleft % 3600) // 60
                time_str = f"{hours}h {minutes}m"
                battery_data['Time Remaining'] = {
                    'value': time_str,
                    'status': 'OK'
                }
            
            return battery_data
            
        except Exception as e:
            self.logger.error(f"Failed to get battery data: {e}")
            return {}
    
    def _get_recent_log_entries(self) -> List[Dict]:
        """Get recent system log entries with errors or warnings."""
        try:
            import subprocess
            import json
            from datetime import datetime, timedelta
            
            log_entries = []
            
            # Get recent journal entries with priority <= 4 (warning or higher)
            try:
                result = subprocess.run(
                    ['journalctl', '--since', '1 hour ago', '-p', '4', '-o', 'json', '-n', '10'],
                    capture_output=True, text=True, timeout=10
                )
                
                for line in result.stdout.split('\n'):
                    if not line.strip():
                        continue
                    
                    try:
                        entry = json.loads(line)
                        
                        # Extract relevant information
                        timestamp = entry.get('__REALTIME_TIMESTAMP', 0)
                        if timestamp:
                            dt = datetime.fromtimestamp(int(timestamp) / 1000000)
                            time_str = dt.strftime('%H:%M:%S')
                        else:
                            time_str = 'Unknown'
                        
                        message = entry.get('MESSAGE', 'No message')
                        priority_str = entry.get('PRIORITY', '6')
                        
                        # Convert priority to integer, default to 6 if conversion fails
                        try:
                            priority = int(priority_str)
                        except (ValueError, TypeError):
                            priority = 6
                        
                        # Determine severity
                        if priority <= 2:
                            severity = 'critical'
                        elif priority <= 4:
                            severity = 'warning'
                        else:
                            continue  # Skip lower priority entries
                        
                        log_entries.append({
                            'timestamp': time_str,
                            'severity': severity,
                            'message': message[:100] + '...' if len(message) > 100 else message
                        })
                        
                    except json.JSONDecodeError:
                        continue
                
            except subprocess.TimeoutExpired:
                log_entries.append({
                    'timestamp': 'Now',
                    'severity': 'warning',
                    'message': 'Log check timeout - unable to retrieve recent entries'
                })
            
            return log_entries
            
        except Exception as e:
            self.logger.error(f"Failed to get log entries: {e}")
            return []
    
    def _on_view_failed_logins(self, button: Gtk.Button) -> None:
        """Handle view failed logins button click."""
        try:
            import subprocess
            
            # Create a dialog to show failed login details
            dialog = Gtk.Dialog(title="Failed Login Attempts", transient_for=self.get_root())
            dialog.set_default_size(700, 500)
            
            # Add buttons
            dialog.add_button("Close", Gtk.ResponseType.CLOSE)
            
            # Create scrolled window for content
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_vexpand(True)
            scrolled.set_hexpand(True)
            
            # Get failed login details
            try:
                result = subprocess.run(
                    ['journalctl', '-u', 'sshd', '--since', '24 hours ago', '-o', 'cat'],
                    capture_output=True, text=True, timeout=10
                )
                
                # Filter for failed login attempts
                failed_lines = []
                for line in result.stdout.split('\n'):
                    if 'Failed password' in line:
                        failed_lines.append(line.strip())
                
                # Create list box for better formatting
                listbox = Gtk.ListBox()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                
                if failed_lines:
                    # Show last 100 entries in a formatted list
                    for line in failed_lines[-100:]:
                        # Create row
                        row = Gtk.ListBoxRow()
                        
                        # Create content box
                        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                        content_box.set_margin_start(8)
                        content_box.set_margin_end(8)
                        content_box.set_margin_top(4)
                        content_box.set_margin_bottom(4)
                        
                        # Create label with monospace font
                        label = Gtk.Label(label=line)
                        label.set_monospace(True)
                        label.set_xalign(0)
                        label.set_wrap(True)
                        content_box.append(label)
                        
                        row.set_child(content_box)
                        listbox.append(row)
                else:
                    # No failed attempts
                    row = Gtk.ListBoxRow()
                    label = Gtk.Label(label="No failed login attempts found in the last 24 hours.")
                    label.set_xalign(0)
                    row.set_child(label)
                    listbox.append(row)
                
                scrolled.set_child(listbox)
                
            except Exception as e:
                error_label = Gtk.Label(label=f"Error retrieving login data: {e}")
                scrolled.set_child(error_label)
            
            # Add scrolled window to dialog
            content_area = dialog.get_content_area()
            content_area.append(scrolled)
            
            dialog.show()
            
        except Exception as e:
            self.logger.error(f"Failed to show failed logins dialog: {e}")
    
    def _on_install_fail2ban(self, button: Gtk.Button) -> None:
        """Handle install fail2ban button click."""
        try:
            # Disable button during installation
            button.set_sensitive(False)
            button.set_label("Installing...")
            
            # Install fail2ban using apt
            def install_complete(success: bool, message: str):
                if success:
                    button.set_label("Installed")
                    # Update the security status after installation
                    GLib.idle_add(self._update_security_status)
                else:
                    button.set_sensitive(True)
                    button.set_label("Install")
                    # Show error dialog
                    dialog = Gtk.MessageDialog(
                        transient_for=self.get_root(),
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="Failed to install fail2ban",
                        secondary_text=message
                    )
                    dialog.run()
                    dialog.destroy()
            
            # Run the installation command with pkexec for proper root prompt
            def run_install():
                try:
                    result = subprocess.run(
                        ['pkexec', 'apt', 'install', '-y', 'fail2ban'],
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minutes timeout for installation
                    )
                    
                    success = result.returncode == 0
                    message = result.stdout if success else result.stderr
                    
                    GLib.idle_add(install_complete, success, message)
                    
                except subprocess.TimeoutExpired:
                    GLib.idle_add(install_complete, False, "Installation timed out")
                except Exception as e:
                    GLib.idle_add(install_complete, False, str(e))
            
            # Run in background thread
            import threading
            thread = threading.Thread(target=run_install, daemon=True)
            thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to install fail2ban: {e}")
            button.set_sensitive(True)
            button.set_label("Install")
    
    def _update_hardware_information(self) -> None:
        """Update hardware information display."""
        try:
            # Clear existing hardware info
            while self.hardware_grid.get_first_child():
                self.hardware_grid.remove(self.hardware_grid.get_first_child())
            
            # Get hardware data
            hardware_data = self._get_hardware_data()
            
            # Add hardware rows
            for i, (item, data) in enumerate(hardware_data.items()):
                # Item name
                name_label = Gtk.Label(label=item)
                name_label.set_xalign(0)
                self.hardware_grid.attach(name_label, 0, i, 1, 1)
                
                # Value
                value_label = Gtk.Label(label=data['value'])
                value_label.set_xalign(0)
                value_label.set_hexpand(True)
                value_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
                value_label.set_max_width_chars(25)  # Limit to 25 characters
                
                # Add tooltip for full text if it's long
                if len(data['value']) > 25:
                    value_label.set_tooltip_text(data['value'])
                
                self.hardware_grid.attach(value_label, 1, i, 1, 1)
                
                # Status indicator (if applicable)
                if 'status' in data:
                    status_label = Gtk.Label(label=data['status'])
                    status_label.add_css_class("pill")
                    status_label.add_css_class(f"pill-{data['status']}")
                    self.hardware_grid.attach(status_label, 2, i, 1, 1)
            
        except Exception as e:
            self.logger.error(f"Failed to update hardware information: {e}")
    
    def _get_hardware_data(self) -> Dict[str, Dict]:
        """Get hardware information data."""
        try:
            import subprocess
            import json
            
            hardware_data = {}
            
            # CPU make/model
            try:
                cpu_info = self.system_monitor._cpu_info_cache
                if cpu_info and 'brand_raw' in cpu_info:
                    cpu_model = cpu_info['brand_raw']
                else:
                    # Fallback to /proc/cpuinfo
                    with open('/proc/cpuinfo', 'r') as f:
                        for line in f:
                            if line.startswith('model name'):
                                cpu_model = line.split(':', 1)[1].strip()
                                break
                        else:
                            cpu_model = "Unknown CPU"
                
                hardware_data['CPU Model'] = {
                    'value': cpu_model,
                    'status': 'OK'
                }
            except Exception:
                hardware_data['CPU Model'] = {
                    'value': 'Unknown CPU',
                    'status': 'unknown'
                }
            
            # Number of monitors
            try:
                result = subprocess.run(
                    ['xrandr', '--listmonitors'],
                    capture_output=True, text=True, timeout=5
                )
                monitor_count = 0
                for line in result.stdout.split('\n'):
                    if line.strip() and not line.startswith('Monitors:'):
                        monitor_count += 1
                
                hardware_data['Monitors'] = {
                    'value': f"{monitor_count} connected",
                    'status': 'OK'
                }
            except Exception:
                hardware_data['Monitors'] = {
                    'value': 'Unable to detect',
                    'status': 'unknown'
                }
            
            # Laptop/Desktop detection and model
            try:
                # Check if it's a laptop
                with open('/sys/class/dmi/id/chassis_type', 'r') as f:
                    chassis_type = f.read().strip()
                
                if chassis_type in ['8', '9', '10', '11', '14']:  # Laptop chassis types
                    device_type = "Laptop"
                    # Try to get laptop model
                    try:
                        with open('/sys/class/dmi/id/product_name', 'r') as f:
                            model = f.read().strip()
                        if model and model != "Default string":
                            device_info = f"{model}"
                        else:
                            device_info = "Unknown model"
                    except:
                        device_info = "Unknown model"
                else:
                    device_type = "Desktop"
                    # Try to get desktop model
                    try:
                        with open('/sys/class/dmi/id/product_name', 'r') as f:
                            model = f.read().strip()
                        if model and model != "Default string":
                            device_info = f"{model}"
                        else:
                            device_info = "Unknown model"
                    except:
                        device_info = "Unknown model"
                
                hardware_data['Device Type'] = {
                    'value': device_type,
                    'status': 'OK'
                }
                
                hardware_data['Device Model'] = {
                    'value': device_info,
                    'status': 'OK'
                }
                
            except Exception:
                hardware_data['Device Type'] = {
                    'value': 'Unknown',
                    'status': 'unknown'
                }
                hardware_data['Device Model'] = {
                    'value': 'Unknown',
                    'status': 'unknown'
                }
            
            # Graphics card
            try:
                result = subprocess.run(
                    ['lspci', '-nn', '-d', '::0300'],
                    capture_output=True, text=True, timeout=5
                )
                gpu_info = []
                for line in result.stdout.split('\n'):
                    if line.strip():
                        # Extract GPU name from lspci output and simplify
                        parts = line.split()
                        if len(parts) >= 2:
                            # Look for the actual GPU name, not the full PCI description
                            gpu_name = ' '.join(parts[2:])
                            
                            # Simplify common GPU names
                            if 'Intel Corporation' in gpu_name:
                                if 'UHD Graphics' in gpu_name:
                                    gpu_name = 'Intel UHD Graphics'
                                elif 'HD Graphics' in gpu_name:
                                    gpu_name = 'Intel HD Graphics'
                                else:
                                    gpu_name = 'Intel Graphics'
                            elif 'NVIDIA Corporation' in gpu_name:
                                if 'GTX' in gpu_name:
                                    gpu_name = 'NVIDIA GTX'
                                elif 'RTX' in gpu_name:
                                    gpu_name = 'NVIDIA RTX'
                                elif 'Quadro' in gpu_name:
                                    gpu_name = 'NVIDIA Quadro'
                                else:
                                    gpu_name = 'NVIDIA Graphics'
                            elif 'AMD' in gpu_name:
                                if 'Radeon' in gpu_name:
                                    gpu_name = 'AMD Radeon'
                                else:
                                    gpu_name = 'AMD Graphics'
                            else:
                                # For other GPUs, take just the first few words
                                words = gpu_name.split()
                                if len(words) > 3:
                                    gpu_name = ' '.join(words[:3]) + '...'
                            
                            gpu_info.append(gpu_name)
                
                if gpu_info:
                    # Remove duplicates and join
                    unique_gpus = list(dict.fromkeys(gpu_info))  # Preserve order
                    hardware_data['Graphics'] = {
                        'value': ', '.join(unique_gpus),
                        'status': 'OK'
                    }
                else:
                    hardware_data['Graphics'] = {
                        'value': 'No dedicated GPU detected',
                        'status': 'OK'
                    }
                    
            except Exception:
                hardware_data['Graphics'] = {
                    'value': 'Unable to detect',
                    'status': 'unknown'
                }
            
            # Input devices
            try:
                mouse_count = 0
                keyboard_count = 0
                
                # Check for mouse devices
                result = subprocess.run(
                    ['find', '/dev/input', '-name', 'mouse*'],
                    capture_output=True, text=True, timeout=5
                )
                mouse_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                
                # Check for keyboard devices
                result = subprocess.run(
                    ['find', '/dev/input', '-name', 'event*'],
                    capture_output=True, text=True, timeout=5
                )
                keyboard_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                
                hardware_data['Input Devices'] = {
                    'value': f"{mouse_count} mouse, {keyboard_count} keyboard",
                    'status': 'OK'
                }
                
            except Exception:
                hardware_data['Input Devices'] = {
                    'value': 'Unable to detect',
                    'status': 'unknown'
                }
            
            return hardware_data
            
        except Exception as e:
            self.logger.error(f"Failed to get hardware data: {e}")
            return {}
    
    def _run_privileged_command(self, command, on_complete=None):
        """Run a command with elevated privileges using pkexec."""
        def run_cmd():
            try:
                if isinstance(command, list):
                    cmd = ['pkexec'] + command
                else:
                    cmd = ['pkexec', 'sh', '-c', command]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                success = result.returncode == 0
                message = result.stdout if success else result.stderr
                
                if on_complete:
                    GLib.idle_add(on_complete, success, message)
                    
            except subprocess.TimeoutExpired:
                if on_complete:
                    GLib.idle_add(on_complete, False, "Command timed out")
            except Exception as e:
                if on_complete:
                    GLib.idle_add(on_complete, False, str(e))
        
        # Run in background thread
        import threading
        thread = threading.Thread(target=run_cmd, daemon=True)
        thread.start()
    
    def cleanup(self) -> None:
        """Clean up resources when the widget is destroyed."""
        self.logger.info("Cleaning up health widget")
        # Any cleanup code would go here 