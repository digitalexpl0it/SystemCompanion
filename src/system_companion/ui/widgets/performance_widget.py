"""
Performance analysis widget for System Companion.

This module provides the performance analysis widget that displays
system performance issues, recommendations, and benchmark results.
"""

import logging
import subprocess
import shutil
from typing import Optional
from datetime import datetime

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio

from ...core.performance_analyzer import PerformanceAnalyzer, PerformanceIssue, PerformanceRecommendation, SystemBenchmark, Severity
from ...utils.exceptions import PerformanceAnalysisError


class PerformanceWidget(Gtk.Box):
    """Performance analysis widget displaying system performance information."""
    
    def __init__(self, system_monitor) -> None:
        """Initialize the performance widget."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        self.logger = logging.getLogger("system_companion.ui.performance_widget")
        self.system_monitor = system_monitor
        self.performance_analyzer = PerformanceAnalyzer(system_monitor)
        
        # Setup UI
        self._setup_ui()
        self._setup_update_timer()
        
        self.logger.info("Performance widget initialized")
    
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
        
        # Performance overview and benchmark row
        overview_benchmark_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        overview_benchmark_row.set_spacing(16)
        
        # Performance overview (left side)
        overview_section = self._create_overview_section()
        overview_section.set_hexpand(True)
        overview_benchmark_row.append(overview_section)
        
        # Benchmark results (right side)
        benchmark_section = self._create_benchmark_section()
        benchmark_section.set_hexpand(True)
        overview_benchmark_row.append(benchmark_section)
        
        content_box.append(overview_benchmark_row)
        
        # Performance issues
        issues_section = self._create_issues_section()
        content_box.append(issues_section)
        
        # Recommendations
        recommendations_section = self._create_recommendations_section()
        content_box.append(recommendations_section)
        
        # Boot performance
        boot_section = self._create_boot_section()
        content_box.append(boot_section)
        
        scrolled_window.set_child(content_box)
        self.append(scrolled_window)
    
    def _create_header(self) -> Gtk.Box:
        """Create the performance header."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.add_css_class("performance-header")
        header_box.set_hexpand(True)

        # Title
        title_label = Gtk.Label(label="Performance Analysis")
        title_label.add_css_class("title-1")
        title_label.set_xalign(0)
        header_box.append(title_label)

        # Spacer to push button to the right
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header_box.append(spacer)

        # Run benchmark button
        self.benchmark_button = Gtk.Button(label="Run Benchmark")
        self.benchmark_button.add_css_class("suggested-action")
        self.benchmark_button.set_hexpand(False)
        self.benchmark_button.connect("clicked", self._on_run_benchmark)
        header_box.append(self.benchmark_button)

        return header_box
    
    def _create_overview_section(self) -> Gtk.Box:
        """Create the performance overview section."""
        overview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        overview_box.add_css_class("dashboard-card")
        
        # Section title
        title_label = Gtk.Label(label="Performance Overview")
        title_label.add_css_class("title-2")
        overview_box.append(title_label)
        
        # Performance metrics grid
        self.overview_grid = Gtk.Grid()
        self.overview_grid.set_row_spacing(12)
        self.overview_grid.set_column_spacing(16)
        
        overview_box.append(self.overview_grid)
        
        return overview_box
    
    def _create_issues_section(self) -> Gtk.Box:
        """Create the performance issues section."""
        issues_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        issues_box.add_css_class("dashboard-card")
        
        # Section title
        title_label = Gtk.Label(label="Performance Issues")
        title_label.add_css_class("title-2")
        issues_box.append(title_label)
        
        # Issues list
        self.issues_listbox = Gtk.ListBox()
        self.issues_listbox.add_css_class("issues-list")
        issues_box.append(self.issues_listbox)
        
        # No issues message
        self.no_issues_label = Gtk.Label(label="No performance issues detected")
        self.no_issues_label.add_css_class("caption")
        self.no_issues_label.add_css_class("dim-label")
        issues_box.append(self.no_issues_label)
        
        return issues_box
    
    def _create_recommendations_section(self) -> Gtk.Box:
        """Create the recommendations section."""
        recommendations_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        recommendations_box.add_css_class("dashboard-card")
        
        # Section title
        title_label = Gtk.Label(label="Optimization Recommendations")
        title_label.add_css_class("title-2")
        recommendations_box.append(title_label)
        
        # Recommendations list
        self.recommendations_listbox = Gtk.ListBox()
        self.recommendations_listbox.add_css_class("recommendations-list")
        recommendations_box.append(self.recommendations_listbox)
        
        return recommendations_box
    
    def _create_boot_section(self) -> Gtk.Box:
        """Create the boot performance section."""
        boot_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        boot_box.add_css_class("dashboard-card")
        
        # Section title
        title_label = Gtk.Label(label="Boot Performance")
        title_label.add_css_class("title-2")
        boot_box.append(title_label)
        
        # Boot performance content
        self.boot_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.boot_content_box.set_spacing(8)
        
        boot_box.append(self.boot_content_box)
        
        return boot_box
    
    def _create_benchmark_section(self) -> Gtk.Box:
        """Create the benchmark section."""
        benchmark_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        benchmark_box.add_css_class("dashboard-card")
        
        # Section title
        title_label = Gtk.Label(label="System Benchmark")
        title_label.add_css_class("title-2")
        benchmark_box.append(title_label)
        
        # Benchmark results
        self.benchmark_results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.benchmark_results_box.set_spacing(8)
        
        # Overall score
        self.overall_score_label = Gtk.Label(label="Overall Score: Not available")
        self.overall_score_label.add_css_class("title-3")
        self.benchmark_results_box.append(self.overall_score_label)
        
        # Score grid
        score_grid = Gtk.Grid()
        score_grid.set_row_spacing(8)
        score_grid.set_column_spacing(16)
        
        # CPU score
        cpu_label = Gtk.Label(label="CPU:")
        cpu_label.set_xalign(0)
        score_grid.attach(cpu_label, 0, 0, 1, 1)
        
        self.cpu_score_label = Gtk.Label(label="N/A")
        score_grid.attach(self.cpu_score_label, 1, 0, 1, 1)
        
        # Memory score
        memory_label = Gtk.Label(label="Memory:")
        memory_label.set_xalign(0)
        score_grid.attach(memory_label, 0, 1, 1, 1)
        
        self.memory_score_label = Gtk.Label(label="N/A")
        score_grid.attach(self.memory_score_label, 1, 1, 1, 1)
        
        # Disk score
        disk_label = Gtk.Label(label="Disk:")
        disk_label.set_xalign(0)
        score_grid.attach(disk_label, 0, 2, 1, 1)
        
        self.disk_score_label = Gtk.Label(label="N/A")
        score_grid.attach(self.disk_score_label, 1, 2, 1, 1)
        
        # Network score
        network_label = Gtk.Label(label="Network:")
        network_label.set_xalign(0)
        score_grid.attach(network_label, 0, 3, 1, 1)
        
        self.network_score_label = Gtk.Label(label="N/A")
        score_grid.attach(self.network_score_label, 1, 3, 1, 1)
        
        self.benchmark_results_box.append(score_grid)
        
        # Last benchmark time
        self.last_benchmark_label = Gtk.Label(label="Last benchmark: Never")
        self.last_benchmark_label.add_css_class("caption")
        self.benchmark_results_box.append(self.last_benchmark_label)
        
        benchmark_box.append(self.benchmark_results_box)
        
        return benchmark_box
    
    def _setup_update_timer(self) -> None:
        """Setup the update timer for performance analysis."""
        # Update immediately
        self._update_performance_analysis()
        
        # Set up timer for periodic updates (every 30 seconds)
        GLib.timeout_add_seconds(30, self._update_performance_analysis)
    
    def _update_performance_analysis(self) -> bool:
        """Update performance analysis and return True to continue the timer."""
        try:
            # Update performance overview
            self._update_performance_overview()
            
            # Update performance issues
            self._update_performance_issues()
            
            # Update recommendations
            self._update_recommendations()
            
            # Update boot performance
            self._update_boot_performance()
            
            # Update benchmark results (if available)
            self._update_benchmark_results()
            
            return True  # Continue the timer
            
        except Exception as e:
            self.logger.error(f"Failed to update performance analysis: {e}")
            return True  # Continue the timer even on error
    
    def _update_performance_issues(self) -> None:
        """Update the performance issues list."""
        try:
            # Clear existing issues
            while self.issues_listbox.get_first_child():
                self.issues_listbox.remove(self.issues_listbox.get_first_child())
            
            # Get current issues
            issues = self.performance_analyzer.analyze_system_performance()
            
            if not issues:
                # Show no issues message
                self.no_issues_label.set_visible(True)
                return
            
            # Hide no issues message
            self.no_issues_label.set_visible(False)
            
            for issue in issues:
                # Create issue row
                row = Gtk.ListBoxRow()
                
                # Issue info box
                info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                info_box.set_margin_start(8)
                info_box.set_margin_end(8)
                info_box.set_margin_top(8)
                info_box.set_margin_bottom(8)
                info_box.set_spacing(4)
                
                # Issue header
                header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                
                # Issue title
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
                
                info_box.append(header_box)
                
                # Issue description
                desc_label = Gtk.Label(label=issue.description)
                desc_label.set_xalign(0)
                desc_label.set_wrap(True)
                info_box.append(desc_label)
                
                # Current vs threshold
                threshold_label = Gtk.Label(label=f"Current: {issue.current_value} | Threshold: {issue.threshold_value}")
                threshold_label.add_css_class("caption")
                threshold_label.set_xalign(0)
                info_box.append(threshold_label)
                
                # Recommendation
                rec_label = Gtk.Label(label=f"Recommendation: {issue.recommendation}")
                rec_label.add_css_class("caption")
                rec_label.set_xalign(0)
                rec_label.set_wrap(True)
                info_box.append(rec_label)
                
                row.set_child(info_box)
                self.issues_listbox.append(row)
            
        except Exception as e:
            self.logger.error(f"Failed to update performance issues: {e}")
    
    def _update_performance_overview(self) -> None:
        """Update the performance overview section."""
        try:
            # Clear existing overview items
            while self.overview_grid.get_first_child():
                self.overview_grid.remove(self.overview_grid.get_first_child())
            
            # Get current performance data
            cpu_info = self.system_monitor.get_cpu_info()
            memory_info = self.system_monitor.get_memory_info()
            disk_info_list = self.system_monitor.get_disk_info()
            network_info_list = self.system_monitor.get_network_info()
            
            # CPU Performance
            cpu_label = Gtk.Label(label="CPU Performance")
            cpu_label.set_xalign(0)
            self.overview_grid.attach(cpu_label, 0, 0, 1, 1)
            
            cpu_status = self._get_performance_status(cpu_info.usage_percent, 80, 90)
            cpu_status_label = Gtk.Label(label=cpu_status['status'])
            cpu_status_label.add_css_class("pill")
            cpu_status_label.add_css_class(f"pill-{cpu_status['status']}")
            self.overview_grid.attach(cpu_status_label, 1, 0, 1, 1)
            
            cpu_details = Gtk.Label(label=f"{cpu_info.usage_percent:.1f}% usage, {cpu_info.core_count} cores")
            cpu_details.set_xalign(0)
            self.overview_grid.attach(cpu_details, 2, 0, 1, 1)
            
            # Memory Performance
            memory_label = Gtk.Label(label="Memory Performance")
            memory_label.set_xalign(0)
            self.overview_grid.attach(memory_label, 0, 1, 1, 1)
            
            memory_status = self._get_performance_status(memory_info.usage_percent, 80, 90)
            memory_status_label = Gtk.Label(label=memory_status['status'])
            memory_status_label.add_css_class("pill")
            memory_status_label.add_css_class(f"pill-{memory_status['status']}")
            self.overview_grid.attach(memory_status_label, 1, 1, 1, 1)
            
            memory_details = Gtk.Label(label=f"{memory_info.usage_percent:.1f}% usage, {memory_info.total_gb:.1f} GB total")
            memory_details.set_xalign(0)
            self.overview_grid.attach(memory_details, 2, 1, 1, 1)
            
            # Disk Performance
            if disk_info_list:
                disk_info = disk_info_list[0]  # Primary disk
                disk_label = Gtk.Label(label="Disk Performance")
                disk_label.set_xalign(0)
                self.overview_grid.attach(disk_label, 0, 2, 1, 1)
                
                disk_status = self._get_performance_status(disk_info.usage_percent, 85, 95)
                disk_status_label = Gtk.Label(label=disk_status['status'])
                disk_status_label.add_css_class("pill")
                disk_status_label.add_css_class(f"pill-{disk_status['status']}")
                self.overview_grid.attach(disk_status_label, 1, 2, 1, 1)
                
                disk_details = Gtk.Label(label=f"{disk_info.usage_percent:.1f}% usage, {disk_info.total_gb:.1f} GB total")
                disk_details.set_xalign(0)
                self.overview_grid.attach(disk_details, 2, 2, 1, 1)
            
            # Network Performance
            if network_info_list:
                network_label = Gtk.Label(label="Network Performance")
                network_label.set_xalign(0)
                self.overview_grid.attach(network_label, 0, 3, 1, 1)
                
                # Count active interfaces (those with IP addresses)
                active_interfaces = len([n for n in network_info_list if n.ip_address != "N/A"])
                network_status = "OK" if active_interfaces > 0 else "warning"
                
                network_status_label = Gtk.Label(label=network_status.upper())
                network_status_label.add_css_class("pill")
                network_status_label.add_css_class(f"pill-{network_status}")
                self.overview_grid.attach(network_status_label, 1, 3, 1, 1)
                
                network_details = Gtk.Label(label=f"{active_interfaces} active interfaces")
                network_details.set_xalign(0)
                self.overview_grid.attach(network_details, 2, 3, 1, 1)
            
        except Exception as e:
            self.logger.error(f"Failed to update performance overview: {e}")
    
    def _get_performance_status(self, current_value: float, warning_threshold: float, critical_threshold: float) -> dict:
        """Get performance status based on current value and thresholds."""
        if current_value >= critical_threshold:
            return {'status': 'critical'}
        elif current_value >= warning_threshold:
            return {'status': 'warning'}
        else:
            return {'status': 'OK'}
    
    def _update_recommendations(self) -> None:
        """Update the recommendations list."""
        try:
            # Clear existing recommendations
            while self.recommendations_listbox.get_first_child():
                self.recommendations_listbox.remove(self.recommendations_listbox.get_first_child())
            
            # Get recommendations
            recommendations = self.performance_analyzer.get_performance_recommendations()
            
            for recommendation in recommendations:
                # Create recommendation row
                row = Gtk.ListBoxRow()
                
                # Recommendation info box
                info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                info_box.set_margin_start(8)
                info_box.set_margin_end(8)
                info_box.set_margin_top(8)
                info_box.set_margin_bottom(8)
                info_box.set_spacing(4)
                
                # Recommendation header
                header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                
                # Title
                title_label = Gtk.Label(label=recommendation.title)
                title_label.add_css_class("title-4")
                title_label.set_xalign(0)
                title_label.set_hexpand(True)
                header_box.append(title_label)
                
                # Category badge
                category_label = Gtk.Label(label=recommendation.category)
                category_label.add_css_class("pill")
                category_label.add_css_class("pill-medium")
                header_box.append(category_label)
                
                info_box.append(header_box)
                
                # Description
                desc_label = Gtk.Label(label=recommendation.description)
                desc_label.set_xalign(0)
                desc_label.set_wrap(True)
                info_box.append(desc_label)
                
                # Impact and difficulty
                impact_label = Gtk.Label(label=f"Impact: {recommendation.impact} | Difficulty: {recommendation.difficulty} | Time: {recommendation.estimated_time}")
                impact_label.add_css_class("caption")
                impact_label.set_xalign(0)
                info_box.append(impact_label)
                
                # Commands
                if recommendation.commands:
                    commands_label = Gtk.Label(label="Commands:")
                    commands_label.add_css_class("caption")
                    commands_label.set_xalign(0)
                    info_box.append(commands_label)
                    
                    for command in recommendation.commands:
                        cmd_label = Gtk.Label(label=f"  {command}")
                        cmd_label.add_css_class("caption")
                        cmd_label.add_css_class("monospace")
                        cmd_label.set_xalign(0)
                        info_box.append(cmd_label)
                
                row.set_child(info_box)
                self.recommendations_listbox.append(row)
            
        except Exception as e:
            self.logger.error(f"Failed to update recommendations: {e}")
    
    def _update_boot_performance(self) -> None:
        """Update the boot performance section."""
        try:
            # Clear existing boot content
            while self.boot_content_box.get_first_child():
                self.boot_content_box.remove(self.boot_content_box.get_first_child())
            
            # Check if systemd-analyze is available and working
            systemd_analyze_available = False
            if shutil.which('systemd-analyze') is not None:
                try:
                    # Test if systemd-analyze actually works
                    result = subprocess.run(
                        ['systemd-analyze', '--version'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    systemd_analyze_available = result.returncode == 0
                except Exception:
                    systemd_analyze_available = False
            
            if not systemd_analyze_available:
                # Show install option
                install_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                install_box.set_spacing(12)
                
                install_label = Gtk.Label(label="systemd-analyze is not available or not working")
                install_label.set_xalign(0)
                install_label.set_hexpand(True)
                install_box.append(install_label)
                
                install_btn = Gtk.Button(label="Install")
                install_btn.add_css_class("suggested-action")
                install_btn.connect("clicked", self._on_install_systemd_analyze)
                install_box.append(install_btn)
                
                self.boot_content_box.append(install_box)
                return
            
            # Get boot time analysis
            try:
                # Get total boot time
                result = subprocess.run(
                    ['systemd-analyze', 'time'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    boot_time_output = result.stdout.strip()
                    
                    # Parse boot time output
                    boot_data = self._parse_boot_time(boot_time_output)
                    
                    # Create boot time display
                    self._create_boot_time_display(boot_data)
                    
                    # Get slowest services
                    self._create_slowest_services_display()
                    
                else:
                    # Show error
                    error_label = Gtk.Label(label="Unable to analyze boot time")
                    error_label.add_css_class("dim-label")
                    self.boot_content_box.append(error_label)
                    
            except subprocess.TimeoutExpired:
                error_label = Gtk.Label(label="Boot analysis timed out")
                error_label.add_css_class("dim-label")
                self.boot_content_box.append(error_label)
            except Exception as e:
                error_label = Gtk.Label(label=f"Boot analysis failed: {e}")
                error_label.add_css_class("dim-label")
                self.boot_content_box.append(error_label)
            
        except Exception as e:
            self.logger.error(f"Failed to update boot performance: {e}")
    
    def _parse_boot_time(self, boot_time_output: str) -> dict:
        """Parse systemd-analyze time output."""
        try:
            # Example: "Startup finished in 4.512s (firmware) + 4.210s (loader) + 1.294s (kernel) + 8.857s (userspace) = 18.875s"
            import re
            
            # Extract total time
            total_match = re.search(r'= (\d+\.\d+)s', boot_time_output)
            total_time = float(total_match.group(1)) if total_match else 0
            
            # Extract individual phases
            phases = {}
            phase_pattern = r'(\d+\.\d+)s \(([^)]+)\)'
            for match in re.finditer(phase_pattern, boot_time_output):
                time_val = float(match.group(1))
                phase_name = match.group(2)
                phases[phase_name] = time_val
            
            return {
                'total': total_time,
                'phases': phases
            }
        except Exception as e:
            self.logger.error(f"Failed to parse boot time: {e}")
            return {'total': 0, 'phases': {}}
    
    def _create_boot_time_display(self, boot_data: dict) -> None:
        """Create boot time display."""
        # Total boot time
        total_label = Gtk.Label(label=f"Total Boot Time: {boot_data['total']:.1f}s")
        total_label.add_css_class("title-3")
        self.boot_content_box.append(total_label)
        
        # Boot time grid
        boot_grid = Gtk.Grid()
        boot_grid.set_row_spacing(8)
        boot_grid.set_column_spacing(16)
        
        # Add phase times
        row = 0
        for phase_name, time_val in boot_data['phases'].items():
            # Phase name
            phase_label = Gtk.Label(label=f"{phase_name.title()}:")
            phase_label.set_xalign(0)
            boot_grid.attach(phase_label, 0, row, 1, 1)
            
            # Time value
            time_label = Gtk.Label(label=f"{time_val:.1f}s")
            boot_grid.attach(time_label, 1, row, 1, 1)
            
            # Status pill
            status = self._get_boot_phase_status(phase_name, time_val)
            status_label = Gtk.Label(label=status['status'])
            status_label.add_css_class("pill")
            status_label.add_css_class(f"pill-{status['status']}")
            boot_grid.attach(status_label, 2, row, 1, 1)
            
            row += 1
        
        self.boot_content_box.append(boot_grid)
    
    def _create_slowest_services_display(self) -> None:
        """Create slowest services display."""
        try:
            # Get slowest services
            result = subprocess.run(
                ['systemd-analyze', 'blame'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse top 5 slowest services
                services = []
                for line in result.stdout.strip().split('\n')[:5]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            time_str = parts[0]
                            service_name = ' '.join(parts[1:])
                            try:
                                time_val = float(time_str.replace('ms', '').replace('s', ''))
                                if 's' in time_str:
                                    time_val *= 1000  # Convert to ms
                                services.append((service_name, time_val))
                            except:
                                continue
                
                if services:
                    # Add separator
                    separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
                    self.boot_content_box.append(separator)
                    
                    # Slowest services title
                    slowest_label = Gtk.Label(label="Slowest Services:")
                    slowest_label.add_css_class("title-4")
                    self.boot_content_box.append(slowest_label)
                    
                    # Services list
                    for service_name, time_ms in services:
                        service_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                        service_box.set_spacing(12)
                        
                        service_label = Gtk.Label(label=service_name)
                        service_label.set_xalign(0)
                        service_label.set_hexpand(True)
                        service_box.append(service_label)
                        
                        time_label = Gtk.Label(label=f"{time_ms:.0f}ms")
                        service_box.append(time_label)
                        
                        self.boot_content_box.append(service_box)
        
        except Exception as e:
            self.logger.error(f"Failed to get slowest services: {e}")
    
    def _get_boot_phase_status(self, phase_name: str, time_val: float) -> dict:
        """Get status for boot phase based on time."""
        # Define thresholds for different phases
        thresholds = {
            'firmware': {'warning': 5.0, 'critical': 10.0},
            'loader': {'warning': 3.0, 'critical': 6.0},
            'kernel': {'warning': 2.0, 'critical': 4.0},
            'userspace': {'warning': 10.0, 'critical': 20.0}
        }
        
        if phase_name in thresholds:
            threshold = thresholds[phase_name]
            if time_val >= threshold['critical']:
                return {'status': 'critical'}
            elif time_val >= threshold['warning']:
                return {'status': 'warning'}
        
        return {'status': 'OK'}
    
    def _on_install_systemd_analyze(self, button: Gtk.Button) -> None:
        """Handle install systemd-analyze button click."""
        try:
            # Disable button during installation
            button.set_sensitive(False)
            button.set_label("Installing...")
            
            # Install systemd-analyze using apt
            def install_complete(success: bool, message: str):
                if success:
                    button.set_label("Installed")
                    # Update the boot performance after installation
                    GLib.idle_add(self._update_boot_performance)
                else:
                    button.set_sensitive(True)
                    button.set_label("Install")
                    # Show error dialog
                    dialog = Gtk.MessageDialog(
                        transient_for=self.get_root(),
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="Failed to install systemd-analyze",
                        secondary_text=message
                    )
                    dialog.run()
                    dialog.destroy()
            
            # Run the installation command with pkexec for proper root prompt
            def run_install():
                try:
                    # First try to install systemd-analyze specifically
                    result = subprocess.run(
                        ['pkexec', 'apt', 'install', '-y', 'systemd-analyze'],
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minutes timeout for installation
                    )
                    
                    # If that fails, try installing the full systemd package
                    if result.returncode != 0:
                        result = subprocess.run(
                            ['pkexec', 'apt', 'install', '-y', 'systemd'],
                            capture_output=True,
                            text=True,
                            timeout=300
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
            self.logger.error(f"Failed to install systemd-analyze: {e}")
            button.set_sensitive(True)
            button.set_label("Install")
    
    def _update_benchmark_results(self) -> None:
        """Update the benchmark results."""
        try:
            benchmark = self.performance_analyzer.get_last_benchmark()
            
            if benchmark:
                # Update overall score
                self.overall_score_label.set_label(f"Overall Score: {benchmark.overall_score:.1f}/100")
                
                # Update individual scores
                self.cpu_score_label.set_label(f"{benchmark.cpu_score:.1f}/100")
                self.memory_score_label.set_label(f"{benchmark.memory_score:.1f}/100")
                self.disk_score_label.set_label(f"{benchmark.disk_score:.1f}/100")
                self.network_score_label.set_label(f"{benchmark.network_score:.1f}/100")
                
                # Update last benchmark time
                time_str = benchmark.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                self.last_benchmark_label.set_label(f"Last benchmark: {time_str}")
            
        except Exception as e:
            self.logger.error(f"Failed to update benchmark results: {e}")
    
    def _on_run_benchmark(self, button: Gtk.Button) -> None:
        """Handle benchmark button click."""
        try:
            # Disable button during benchmark
            button.set_sensitive(False)
            button.set_label("Running Benchmark...")
            
            # Create progress dialog
            self.progress_dialog = Gtk.Dialog(
                title="System Benchmark Progress",
                transient_for=self.get_root(),
                modal=True
            )
            
            # Add progress bar and label
            progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            progress_box.set_margin_start(20)
            progress_box.set_margin_end(20)
            progress_box.set_margin_top(20)
            progress_box.set_margin_bottom(20)
            progress_box.set_spacing(12)
            
            self.progress_label = Gtk.Label(label="Starting benchmark...")
            progress_box.append(self.progress_label)
            
            self.progress_bar = Gtk.ProgressBar()
            self.progress_bar.set_fraction(0.0)
            progress_box.append(self.progress_bar)
            
            self.progress_dialog.get_content_area().append(progress_box)
            
            # Show dialog
            self.progress_dialog.present()
            
            # Progress callback function
            def progress_callback(message: str, percentage: int):
                def update_progress():
                    self.progress_label.set_label(message)
                    self.progress_bar.set_fraction(percentage / 100.0)
                    return False
                GLib.idle_add(update_progress)
            
            # Run benchmark in background
            def run_benchmark():
                try:
                    benchmark = self.performance_analyzer.run_system_benchmark(progress_callback)
                    
                    # Update UI in main thread
                    GLib.idle_add(self._benchmark_completed, benchmark)
                    
                except Exception as e:
                    self.logger.error(f"Benchmark failed: {e}")
                    GLib.idle_add(self._benchmark_failed, str(e))
            
            # Start benchmark thread
            import threading
            thread = threading.Thread(target=run_benchmark)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to start benchmark: {e}")
            button.set_sensitive(True)
            button.set_label("Run Benchmark")
    
    def _benchmark_completed(self, benchmark: SystemBenchmark) -> None:
        """Handle benchmark completion."""
        try:
            # Close progress dialog
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.destroy()
                delattr(self, 'progress_dialog')
            
            # Re-enable button
            self.benchmark_button.set_sensitive(True)
            self.benchmark_button.set_label("Run Benchmark")
            
            # Update results
            self._update_benchmark_results()
            
            # Show completion message
            self._show_notification("Benchmark completed", f"Overall score: {benchmark.overall_score:.1f}/100")
            
        except Exception as e:
            self.logger.error(f"Failed to handle benchmark completion: {e}")
    
    def _benchmark_failed(self, error_message: str) -> None:
        """Handle benchmark failure."""
        try:
            # Close progress dialog
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.destroy()
                delattr(self, 'progress_dialog')
            
            # Re-enable button
            self.benchmark_button.set_sensitive(True)
            self.benchmark_button.set_label("Run Benchmark")
            
            # Show error message
            self._show_notification("Benchmark failed", error_message)
            
        except Exception as e:
            self.logger.error(f"Failed to handle benchmark failure: {e}")
    
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
        self.logger.info("Cleaning up performance widget")
        # Any cleanup code would go here 