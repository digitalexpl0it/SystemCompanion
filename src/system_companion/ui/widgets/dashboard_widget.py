"""
Dashboard widget for System Companion.

This module provides the main dashboard widget that displays
real-time system monitoring information.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
import os

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('cairo', '1.0')
from gi.repository import Gtk, Adw, GLib, Gio, cairo, Gdk

from ...core.system_monitor import SystemMonitor, CPUInfo, MemoryInfo, DiskInfo, NetworkInfo
from ...utils.exceptions import MonitoringError
from .chart_widget import ChartWidget
from .multi_core_chart_widget import MultiCoreChartWidget
from .multi_interface_chart_widget import MultiInterfaceChartWidget
from .network_interface_chart_widget import NetworkInterfaceChartWidget
from .disconnected_interface_widget import DisconnectedInterfaceWidget


class DashboardWidget(Gtk.Box):
    """Main dashboard widget displaying system monitoring information."""
    
    def __init__(self) -> None:
        """Initialize the dashboard widget."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        self.logger = logging.getLogger("system_companion.ui.dashboard_widget")
        self.system_monitor = SystemMonitor()
        
        # Chart widgets
        self.cpu_chart = None  # Will be MultiCoreChartWidget
        self.memory_chart = None
        self.disk_chart = None
        self.network_chart = None  # Will be replaced with individual interface charts
        self.network_interface_charts = {}  # Dictionary to store individual interface charts
        self.disconnected_interface_widgets = {}  # Dictionary to store disconnected interface widgets
        
        # Data storage for charts
        self.cpu_history = [0.0] * 15  # Initialize with 15 zero values
        self.memory_history = [0.0] * 15  # Initialize with 15 zero values
        self.max_history_points = 60  # 1 minute at 1-second intervals
        
        # Setup UI
        self._setup_ui()
        self._setup_update_timer()
        
        self.logger.info("Dashboard widget initialized")
    
    def _setup_ui(self) -> None:
        """Setup the user interface with tabs."""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_spacing(16)
        
        # Header
        header = self._create_header()
        main_box.append(header)
        
        # Create tab switcher header
        tab_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        tab_header.set_margin_bottom(8)
        tab_header.add_css_class("dashboard-tab-bar")
        
        # Create tab buttons manually for custom styling
        self.tab_buttons = []
        tab_names = [
            ("cpu", "CPU"),
            ("memory", "Memory"),
            ("disk", "Disk"),
            ("network", "Network"),
            ("processes", "Processes")
        ]
        for idx, (tab_id, tab_label) in enumerate(tab_names):
            btn = Gtk.Button(label=tab_label)
            btn.add_css_class("dashboard-tab-btn")
            if idx == 0:
                btn.add_css_class("active")
            btn.connect("clicked", self._on_tab_button_clicked, tab_id)
            tab_header.append(btn)
            self.tab_buttons.append(btn)
        
        main_box.append(tab_header)
        
        # Remove the divider line under tabs
        # divider = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        # divider.set_margin_bottom(8)
        # divider.add_css_class("tab-divider")
        # main_box.append(divider)
        
        # Create tab view
        self.tab_view = Adw.ViewStack()
        self.tab_view.set_vexpand(True)
        self.tab_view.set_hexpand(True)
        self.tab_view.add_css_class("modern-tab-view")
        
        # Create tabs with modern icons
        self._create_cpu_tab()
        self._create_memory_tab()
        self._create_disk_tab()
        self._create_network_tab()
        self._create_processes_tab()
        
        # Add tab pages to stack
        self.tab_view.set_visible_child_name("cpu")
        main_box.append(self.tab_view)
        self.append(main_box)

    def _on_tab_button_clicked(self, button, tab_id):
        # Remove 'active' class from all buttons
        for btn in self.tab_buttons:
            btn.remove_css_class("active")
        # Add 'active' class to the clicked button
        button.add_css_class("active")
        # Switch the tab view
        self.tab_view.set_visible_child_name(tab_id)
    
    def _create_header(self) -> Gtk.Box:
        """Create the dashboard header."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.add_css_class("dashboard-header")
        
        # Title
        title_label = Gtk.Label(label="System Dashboard")
        title_label.add_css_class("title-1")
        title_label.set_hexpand(True)
        title_label.set_xalign(0)
        header_box.append(title_label)
        
        # Last updated
        self.last_updated_label = Gtk.Label(label="Last updated: Never")
        self.last_updated_label.add_css_class("caption")
        self.last_updated_label.set_hexpand(False)
        header_box.append(self.last_updated_label)
        
        return header_box
    
    def _create_health_overview(self) -> Gtk.Box:
        """Create the system health overview section."""
        health_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        health_box.add_css_class("dashboard-card")
        
        # Health score
        self.health_score_label = Gtk.Label(label="System Health: Loading...")
        self.health_score_label.add_css_class("title-2")
        health_box.append(self.health_score_label)
        
        # Health bar
        self.health_bar = Gtk.ProgressBar()
        self.health_bar.set_show_text(True)
        self.health_bar.set_fraction(0.0)
        health_box.append(self.health_bar)
        
        return health_box
    
    def _create_metrics_grid(self) -> Gtk.Grid:
        """Create the metrics grid."""
        grid = Gtk.Grid()
        grid.set_row_spacing(16)
        grid.set_column_spacing(16)
        grid.add_css_class("metrics-grid")
        
        # CPU metrics
        cpu_card = self._create_metric_card("CPU Usage", "0%", "cpu-metric")
        grid.attach(cpu_card, 0, 0, 1, 1)
        
        # Memory metrics
        memory_card = self._create_metric_card("Memory Usage", "0 GB / 0 GB", "memory-metric")
        grid.attach(memory_card, 1, 0, 1, 1)
        
        # Disk metrics
        disk_card = self._create_metric_card("Disk Usage", "0 GB / 0 GB", "disk-metric")
        grid.attach(disk_card, 0, 1, 1, 1)
        
        # Network metrics
        network_card = self._create_metric_card("Network", "0 Mbps", "network-metric")
        grid.attach(network_card, 1, 1, 1, 1)
        
        # Store references for updates
        self.cpu_metric = cpu_card
        self.memory_metric = memory_card
        self.disk_metric = disk_card
        self.network_metric = network_card
        
        return grid
    
    def _create_metric_card(self, title: str, value: str, css_class: str) -> Gtk.Box:
        """Create a metric card widget."""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("dashboard-card")
        card.add_css_class(css_class)
        
        # Title
        title_label = Gtk.Label(label=title)
        title_label.add_css_class("caption")
        card.append(title_label)
        
        # Value
        value_label = Gtk.Label(label=value)
        value_label.add_css_class("title-3")
        value_label.set_name(f"{css_class}-value")
        card.append(value_label)
        
        # Chart widget - use MultiCoreChartWidget for CPU, regular ChartWidget for others
        if css_class == "cpu-metric":
            chart = MultiCoreChartWidget(title=title, max_points=15)  # More data points for mini graphs
            chart.set_size_request(-1, 120)  # Slightly taller for multi-core
            self.cpu_chart = chart
        elif css_class == "disk-metric":
            # Create multi-series chart for disk IOPS
            chart = ChartWidget(title=title, max_points=3, series_names=["Read", "Write"])
            chart.set_size_request(-1, 100)
            self.disk_chart = chart
        else:
            chart = ChartWidget(title=title, max_points=3)
            chart.set_size_request(-1, 100)
        
        chart.set_margin_top(8)
        chart.set_margin_bottom(8)
        chart.set_vexpand(False)
        chart.set_hexpand(True)
        
        # Add CSS class for styling
        chart.add_css_class("metric-chart")
        
        # Store chart references
        if css_class == "memory-metric":
            self.memory_chart = chart
        elif css_class == "network-metric":
            # Create multi-interface chart for network
            chart = MultiInterfaceChartWidget(title=title, max_points=3)
            chart.set_size_request(-1, 100)
            chart.set_margin_top(8)
            chart.set_margin_bottom(8)
            chart.set_vexpand(False)
            chart.set_hexpand(True)
            chart.add_css_class("metric-chart")
            self.network_chart = chart
        
        card.append(chart)
        
        return card
    
    def _create_cpu_tab(self) -> None:
        """Create the CPU monitoring tab."""
        # Create scrolled container
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        scrolled_window.add_css_class("dashboard-scroll-bg")
        
        # Create content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_spacing(16)
        content_box.set_margin_start(16)
        content_box.set_margin_end(16)
        content_box.set_margin_top(16)
        content_box.set_margin_bottom(16)
        content_box.add_css_class("dashboard-content-bg")
        
        # Outer card for summary and chart
        outer_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer_card.add_css_class("dashboard-outer-card")
        outer_card.set_spacing(16)
        outer_card.set_margin_top(0)
        outer_card.set_margin_bottom(0)
        outer_card.set_margin_start(0)
        outer_card.set_margin_end(0)
        
        # CPU usage summary
        cpu_summary = self._create_cpu_summary()
        outer_card.append(cpu_summary)
        
        # CPU chart (full size) with more data points for detailed view
        self.cpu_chart = MultiCoreChartWidget(title="", max_points=20)
        self.cpu_chart.set_vexpand(True)
        self.cpu_chart.set_hexpand(True)
        self.cpu_chart.set_size_request(600, 400)
        self.cpu_chart.add_css_class("cpu-chart")
        outer_card.append(self.cpu_chart)
        
        content_box.append(outer_card)
        
        scrolled_window.set_child(content_box)
        
        # Add to tab view with blue CPU icon
        self.tab_view.add_titled(scrolled_window, "cpu", "CPU")
        # Set icon for CPU tab (blue processor icon)
        self.tab_view.get_page(scrolled_window).set_icon_name("processor-symbolic")
    
    def _create_cpu_summary(self) -> Gtk.Box:
        """Create CPU summary information."""
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        summary_box.add_css_class("dashboard-card")
        summary_box.add_css_class("dashboard-main-card")
        
        # Create main horizontal layout for Group 1 and Group 2
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.set_spacing(20)
        main_box.set_margin_bottom(16)
        
        # Group 1: Left side - Large CPU icon and main info
        group1_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        group1_box.set_spacing(12)
        
        # Left side - Large CPU icon
        icon_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        icon_box.set_halign(Gtk.Align.START)
        icon_box.set_valign(Gtk.Align.START)
        
        # Load CPU icon from resources
        try:
            # Try multiple paths to find the CPU icon
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '..', '..', '..', 'resources', 'icons', 'cpu.png'),
                os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'resources', 'icons', 'cpu.png'),
                'resources/icons/cpu.png',
                '/usr/share/system-companion/resources/icons/cpu.png'
            ]
            
            icon_loaded = False
            for icon_path in possible_paths:
                if os.path.exists(icon_path):
                    cpu_icon = Gtk.Picture()
                    cpu_icon.set_filename(icon_path)
                    cpu_icon.set_size_request(64, 64)  # Larger icon
                    icon_box.append(cpu_icon)
                    icon_loaded = True
                    break
            
            if not icon_loaded:
                # Fallback to a simple label if icon not found
                fallback_icon = Gtk.Label(label="🖥️")
                fallback_icon.add_css_class("title-1")
                fallback_icon.set_size_request(64, 64)
                icon_box.append(fallback_icon)
        except Exception as e:
            # Fallback to a simple label if icon loading fails
            fallback_icon = Gtk.Label(label="🖥️")
            fallback_icon.add_css_class("title-1")
            fallback_icon.set_size_request(64, 64)
            icon_box.append(fallback_icon)
        
        group1_box.append(icon_box)
        
        # Group 1: Main CPU info (right of icon)
        group1_info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        group1_info_box.set_spacing(8)
        
        # CPU usage percentage
        self.cpu_usage_label = Gtk.Label(label="CPU Usage: 0%")
        self.cpu_usage_label.add_css_class("title-2")
        group1_info_box.append(self.cpu_usage_label)

        # CPU model info
        self.cpu_model_label = Gtk.Label(label="Loading CPU information...")
        self.cpu_model_label.add_css_class("caption")
        group1_info_box.append(self.cpu_model_label)

        # CPU architecture
        self.cpu_arch_label = Gtk.Label(label="Architecture: Loading...")
        self.cpu_arch_label.add_css_class("caption")
        group1_info_box.append(self.cpu_arch_label)

        # CPU cache info
        self.cpu_cache_label = Gtk.Label(label="Cache: Loading...")
        self.cpu_cache_label.add_css_class("caption")
        group1_info_box.append(self.cpu_cache_label)
        
        group1_box.append(group1_info_box)
        main_box.append(group1_box)
        
        # Group 2: Right side - Detailed specifications in two sections
        group2_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        group2_box.set_hexpand(True)
        group2_box.set_spacing(8)
        
        # Group 2: Detailed specifications grid with labels
        specs_grid = Gtk.Grid()
        specs_grid.set_column_spacing(32)
        specs_grid.set_row_spacing(4)
        specs_grid.set_margin_top(12)

        # Section 1: Left column with labels and values
        # CPU Speed (Current)
        speed_label = Gtk.Label(label="CPU Speed (Current):")
        speed_label.add_css_class("caption")
        specs_grid.attach(speed_label, 0, 0, 1, 1)
        self.cpu_speed_label = Gtk.Label(label="Loading...")
        self.cpu_speed_label.add_css_class("caption")
        specs_grid.attach(self.cpu_speed_label, 1, 0, 1, 1)

        # CPU Base Speed
        base_speed_label = Gtk.Label(label="CPU Base Speed:")
        base_speed_label.add_css_class("caption")
        specs_grid.attach(base_speed_label, 0, 1, 1, 1)
        self.cpu_base_speed_label = Gtk.Label(label="Loading...")
        self.cpu_base_speed_label.add_css_class("caption")
        specs_grid.attach(self.cpu_base_speed_label, 1, 1, 1, 1)

        # Sockets
        sockets_label = Gtk.Label(label="Sockets:")
        sockets_label.add_css_class("caption")
        specs_grid.attach(sockets_label, 0, 2, 1, 1)
        self.sockets_label = Gtk.Label(label="Loading...")
        self.sockets_label.add_css_class("caption")
        specs_grid.attach(self.sockets_label, 1, 2, 1, 1)

        # Cores (Physical)
        cores_label = Gtk.Label(label="Cores (Physical):")
        cores_label.add_css_class("caption")
        specs_grid.attach(cores_label, 0, 3, 1, 1)
        self.physical_cores_label = Gtk.Label(label="Loading...")
        self.physical_cores_label.add_css_class("caption")
        specs_grid.attach(self.physical_cores_label, 1, 3, 1, 1)

        # Logical Processors
        logical_label = Gtk.Label(label="Logical Processors:")
        logical_label.add_css_class("caption")
        specs_grid.attach(logical_label, 0, 4, 1, 1)
        self.logical_processors_label = Gtk.Label(label="Loading...")
        self.logical_processors_label.add_css_class("caption")
        specs_grid.attach(self.logical_processors_label, 1, 4, 1, 1)

        # Section 2: Right column with labels and values
        # Process Count
        process_label = Gtk.Label(label="Process Count:")
        process_label.add_css_class("caption")
        specs_grid.attach(process_label, 2, 0, 1, 1)
        self.process_count_label = Gtk.Label(label="Loading...")
        self.process_count_label.add_css_class("caption")
        specs_grid.attach(self.process_count_label, 3, 0, 1, 1)

        # Thread Count
        thread_label = Gtk.Label(label="Thread Count:")
        thread_label.add_css_class("caption")
        specs_grid.attach(thread_label, 2, 1, 1, 1)
        self.thread_count_label = Gtk.Label(label="Loading...")
        self.thread_count_label.add_css_class("caption")
        specs_grid.attach(self.thread_count_label, 3, 1, 1, 1)

        # Zombie Processes
        zombie_label = Gtk.Label(label="Zombie Processes:")
        zombie_label.add_css_class("caption")
        specs_grid.attach(zombie_label, 2, 2, 1, 1)
        self.zombie_processes_label = Gtk.Label(label="Loading...")
        self.zombie_processes_label.add_css_class("caption")
        specs_grid.attach(self.zombie_processes_label, 3, 2, 1, 1)

        # Uptime
        uptime_label = Gtk.Label(label="Uptime:")
        uptime_label.add_css_class("caption")
        specs_grid.attach(uptime_label, 2, 3, 1, 1)
        self.uptime_label = Gtk.Label(label="Loading...")
        self.uptime_label.add_css_class("caption")
        specs_grid.attach(self.uptime_label, 3, 3, 1, 1)

        # Virtualization
        virtualization_label = Gtk.Label(label="Virtualization:")
        virtualization_label.add_css_class("caption")
        specs_grid.attach(virtualization_label, 2, 4, 1, 1)
        self.virtualization_label = Gtk.Label(label="Loading...")
        self.virtualization_label.add_css_class("caption")
        specs_grid.attach(self.virtualization_label, 3, 4, 1, 1)

        group2_box.append(specs_grid)
        main_box.append(group2_box)
        summary_box.append(main_box)
        return summary_box
    
    def _create_memory_tab(self) -> None:
        """Create the memory monitoring tab."""
        # Create scrolled container
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        scrolled_window.add_css_class("dashboard-scroll-bg")
        
        # Create content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_spacing(16)
        content_box.set_margin_start(16)
        content_box.set_margin_end(16)
        content_box.set_margin_top(16)
        content_box.set_margin_bottom(16)
        content_box.add_css_class("dashboard-content-bg")
        
        # Memory summary
        memory_summary = self._create_memory_summary()
        content_box.append(memory_summary)
        
        # Memory chart (full size)
        self.memory_chart = ChartWidget(title="Memory Usage", max_points=60)
        self.memory_chart.set_vexpand(True)
        self.memory_chart.set_hexpand(True)
        self.memory_chart.set_size_request(600, 400)
        self.memory_chart.add_css_class("memory-chart")
        content_box.append(self.memory_chart)
        
        scrolled_window.set_child(content_box)
        
        # Add to tab view with blue memory icon
        self.tab_view.add_titled(scrolled_window, "memory", "Memory")
        # Set icon for Memory tab (blue memory icon)
        self.tab_view.get_page(scrolled_window).set_icon_name("drive-harddisk-symbolic")
    
    def _create_memory_summary(self) -> Gtk.Box:
        """Create memory summary information."""
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        summary_box.add_css_class("dashboard-card")
        
        # Main memory usage
        self.memory_usage_label = Gtk.Label(label="Memory Usage: 0 GB / 0 GB")
        self.memory_usage_label.add_css_class("title-2")
        summary_box.append(self.memory_usage_label)
        
        # Memory percentage
        self.memory_percent_label = Gtk.Label(label="Usage: 0%")
        self.memory_percent_label.add_css_class("caption")
        summary_box.append(self.memory_percent_label)
        
        # Swap usage (if available)
        self.swap_usage_label = Gtk.Label(label="Swap: 0 GB / 0 GB")
        self.swap_usage_label.add_css_class("caption")
        summary_box.append(self.swap_usage_label)
        
        return summary_box
    
    def _create_disk_tab(self) -> None:
        """Create the disk monitoring tab."""
        # Create scrolled container
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        scrolled_window.add_css_class("dashboard-scroll-bg")
        
        # Create content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_spacing(16)
        content_box.set_margin_start(16)
        content_box.set_margin_end(16)
        content_box.set_margin_top(16)
        content_box.set_margin_bottom(16)
        content_box.add_css_class("dashboard-content-bg")
        
        # Disk summary
        disk_summary = self._create_disk_summary()
        content_box.append(disk_summary)
        
        # Disk partitions section
        disk_partitions = self._create_disk_partitions()
        content_box.append(disk_partitions)
        
        # Disk chart (full size) - shows IOPS with separate read/write lines
        self.disk_chart = ChartWidget(title="Disk IOPS", max_points=60, series_names=["Read", "Write"])
        self.disk_chart.set_vexpand(True)
        self.disk_chart.set_hexpand(True)
        self.disk_chart.set_size_request(600, 400)
        self.disk_chart.add_css_class("disk-chart")
        content_box.append(self.disk_chart)
        
        scrolled_window.set_child(content_box)
        
        # Add to tab view with blue disk icon
        self.tab_view.add_titled(scrolled_window, "disk", "Disk")
        # Set icon for Disk tab (blue disk icon)
        self.tab_view.get_page(scrolled_window).set_icon_name("drive-removable-media-symbolic")
    
    def _create_disk_summary(self) -> Gtk.Box:
        """Create disk summary information."""
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        summary_box.add_css_class("dashboard-card")
        
        # Disk usage
        self.disk_usage_label = Gtk.Label(label="Disk Usage: 0 GB / 0 GB")
        self.disk_usage_label.add_css_class("title-2")
        summary_box.append(self.disk_usage_label)
        
        # Disk percentage with label
        self.disk_percent_label = Gtk.Label(label="Usage: 0%")
        self.disk_percent_label.add_css_class("caption")
        summary_box.append(self.disk_percent_label)
        
        return summary_box
    
    def _create_disk_partitions(self) -> Gtk.Box:
        """Create disk partitions section with progress bars in two columns."""
        partitions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        partitions_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="Filesystems")
        title_label.add_css_class("title-2")
        partitions_box.append(title_label)
        
        # Container for partition items in two columns
        self.partitions_container = Gtk.Grid()
        self.partitions_container.set_column_spacing(16)
        self.partitions_container.set_row_spacing(8)
        partitions_box.append(self.partitions_container)
        
        return partitions_box
    
    def _create_partition_item(self, device: str, mountpoint: str, used_gb: float, total_gb: float, usage_percent: float) -> Gtk.Box:
        """Create a compact partition item with progress bar."""
        item_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        item_box.set_spacing(4)
        item_box.set_margin_start(8)
        item_box.set_margin_end(8)
        item_box.set_margin_top(4)
        item_box.set_margin_bottom(4)
        
        # Top row: device name and usage percentage
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        top_row.set_spacing(8)
        
        # Device name (shortened)
        device_short = device.replace('/dev/', '')
        device_label = Gtk.Label(label=device_short)
        device_label.add_css_class("caption")
        device_label.set_halign(Gtk.Align.START)
        top_row.append(device_label)
        
        # Mount point (shortened)
        mount_short = mountpoint if mountpoint == '/' else mountpoint.split('/')[-1] if mountpoint.split('/')[-1] else mountpoint
        mount_label = Gtk.Label(label=f"({mount_short})")
        mount_label.add_css_class("caption")
        mount_label.set_halign(Gtk.Align.START)
        top_row.append(mount_label)
        
        # Usage percentage
        percent_label = Gtk.Label(label=f"{usage_percent:.1f}%")
        percent_label.add_css_class("caption")
        percent_label.set_halign(Gtk.Align.END)
        percent_label.set_hexpand(True)
        top_row.append(percent_label)
        
        item_box.append(top_row)
        
        # Progress bar
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_fraction(usage_percent / 100.0)
        progress_bar.set_size_request(-1, 6)
        
        # Color the progress bar based on usage
        if usage_percent >= 90:
            progress_bar.add_css_class("critical")
        elif usage_percent >= 75:
            progress_bar.add_css_class("warning")
        else:
            progress_bar.add_css_class("normal")
        
        item_box.append(progress_bar)
        
        # Bottom row: used/total space
        bottom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        bottom_row.set_spacing(8)
        
        # Used space
        used_label = Gtk.Label(label=f"{used_gb:.1f}G")
        used_label.add_css_class("caption")
        used_label.set_halign(Gtk.Align.START)
        bottom_row.append(used_label)
        
        # Total space
        total_label = Gtk.Label(label=f"/ {total_gb:.1f}G")
        total_label.add_css_class("caption")
        total_label.set_halign(Gtk.Align.END)
        total_label.set_hexpand(True)
        bottom_row.append(total_label)
        
        item_box.append(bottom_row)
        
        return item_box
    
    def _create_network_tab(self) -> None:
        """Create the network monitoring tab."""
        # Create scrolled container
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        scrolled_window.add_css_class("dashboard-scroll-bg")
        
        # Create content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_spacing(16)
        content_box.set_margin_start(16)
        content_box.set_margin_end(16)
        content_box.set_margin_top(16)
        content_box.set_margin_bottom(16)
        content_box.add_css_class("dashboard-content-bg")
        
        # Network summary
        network_summary = self._create_network_summary()
        content_box.append(network_summary)
        
        # Create container for individual interface charts
        self.network_charts_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.network_charts_container.set_spacing(16)
        
        # Add placeholder for dynamic charts
        placeholder_label = Gtk.Label(label="Loading network interfaces...")
        placeholder_label.add_css_class("title-2")
        self.network_charts_container.append(placeholder_label)
        
        content_box.append(self.network_charts_container)
        
        scrolled_window.set_child(content_box)
        
        # Add to tab view with blue network icon
        self.tab_view.add_titled(scrolled_window, "network", "Network")
        # Set icon for Network tab (blue network icon)
        self.tab_view.get_page(scrolled_window).set_icon_name("network-wireless-symbolic")
    
    def _create_network_summary(self) -> Gtk.Box:
        """Create network summary information."""
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        summary_box.add_css_class("dashboard-card")
        
        # Network usage title
        network_title = Gtk.Label(label="Network Usage")
        network_title.add_css_class("title-2")
        summary_box.append(network_title)
        
        # Network speed (main display)
        self.network_speed_label = Gtk.Label(label="0.000 Mbps")
        self.network_speed_label.add_css_class("caption")
        summary_box.append(self.network_speed_label)
        
        return summary_box
    
    def _create_processes_tab(self) -> None:
        """Create the processes monitoring tab."""
        # Create scrolled container
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        scrolled_window.add_css_class("dashboard-scroll-bg")
        
        # Create content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_spacing(16)
        content_box.set_margin_start(16)
        content_box.set_margin_end(16)
        content_box.set_margin_top(16)
        content_box.set_margin_bottom(16)
        content_box.add_css_class("dashboard-content-bg")
        
        # Top processes section
        top_processes = self._create_top_processes()
        content_box.append(top_processes)
        
        # User processes table section
        user_processes = self._create_user_processes_table()
        content_box.append(user_processes)
        
        scrolled_window.set_child(content_box)
        
        # Add to tab view with blue processes icon
        self.tab_view.add_titled(scrolled_window, "processes", "Processes")
        # Set icon for Processes tab (blue processes icon)
        self.tab_view.get_page(scrolled_window).set_icon_name("utilities-system-monitor-symbolic")
    
    def _create_top_processes(self) -> Gtk.Box:
        """Create the top processes section."""
        process_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        process_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="Top Processes")
        title_label.add_css_class("title-2")
        process_box.append(title_label)
        
        # Process list
        self.process_listbox = Gtk.ListBox()
        self.process_listbox.add_css_class("process-list")
        process_box.append(self.process_listbox)
        
        return process_box
    
    def _create_user_processes_table(self) -> Gtk.Box:
        """Create the user processes table section."""
        table_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        table_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="Your Processes")
        title_label.add_css_class("title-2")
        table_box.append(title_label)
        
        # Create tree view for process table
        self._create_process_treeview(table_box)
        
        return table_box
    
    def _create_process_treeview(self, parent_box: Gtk.Box) -> None:
        """Create the process tree view with columns."""
        # Create scrolled window for tree view
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        scrolled_window.set_size_request(800, 400)
        self.process_treeview_scrolled_window = scrolled_window  # Store reference for scroll position
        
        # Create tree store with sorting
        self.process_store = Gtk.TreeStore.new([
            str,  # Process Name
            str,  # User
            str,  # % CPU
            str,  # ID
            str,  # Memory
            str,  # Disk Read
            str,  # Disk Write
            str,  # Priority
            int,  # PID (for kill functionality)
        ])
        
        # Store selected PID to maintain selection during refresh
        self.selected_pid = None
        
        # Store sort order to maintain sorting during refresh
        self.current_sort_column = 4  # Default: Memory column
        self.current_sort_order = Gtk.SortType.DESCENDING  # Default: Descending
        
        # Enable sorting
        self.process_store.set_sort_func(0, self._sort_string_column, 0)  # Process Name
        self.process_store.set_sort_func(1, self._sort_string_column, 1)  # User
        self.process_store.set_sort_func(2, self._sort_cpu_column, 2)     # % CPU
        self.process_store.set_sort_func(3, self._sort_pid_column, 3)     # ID
        self.process_store.set_sort_func(4, self._sort_memory_column, 4)  # Memory
        self.process_store.set_sort_func(5, self._sort_disk_column, 5)    # Disk Read
        self.process_store.set_sort_func(6, self._sort_disk_column, 6)    # Disk Write
        self.process_store.set_sort_func(7, self._sort_priority_column, 7) # Priority
        
        # Create tree view
        self.process_treeview = Gtk.TreeView.new_with_model(self.process_store)
        self.process_treeview.set_headers_visible(True)
        self.process_treeview.set_rubber_banding(True)
        
        # Create columns
        columns = [
            ("Process Name", 0, 200),
            ("User", 1, 100),
            ("% CPU", 2, 80),
            ("ID", 3, 80),
            ("Memory", 4, 100),
            ("Disk Read", 5, 100),
            ("Disk Write", 6, 100),
            ("Priority", 7, 80)
        ]
        
        for title, column_id, width in columns:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=column_id)
            column.set_min_width(width)
            column.set_resizable(True)
            column.set_sort_column_id(column_id)
            self.process_treeview.append_column(column)
        
        # Add right-click context menu using Gtk.GestureClick (GTK4)
        gesture = Gtk.GestureClick.new()
        gesture.connect("pressed", self._on_process_treeview_right_click)
        self.process_treeview.add_controller(gesture)
        
        # Set default sort order (by memory usage, descending)
        self.process_store.set_sort_column_id(4, Gtk.SortType.DESCENDING)
        
        # Add to parent
        scrolled_window.set_child(self.process_treeview)
        parent_box.append(scrolled_window)
        
        # Connect selection changed signal to track selected PID
        selection = self.process_treeview.get_selection()
        selection.connect("changed", self._on_selection_changed)
        
        # Connect sort changed signal to track sort order
        self.process_store.connect("sort-column-changed", self._on_sort_changed)
    
    def _on_kill_process_clicked(self, button: Gtk.Button) -> None:
        """Handle kill process button click."""
        try:
            selection = self.process_treeview.get_selection()
            model, treeiter = selection.get_selected()
            
            if treeiter is None:
                return
            
            # Get PID from the last column
            pid = model.get_value(treeiter, 10)  # PID column
            process_name = model.get_value(treeiter, 0)  # Process name
            
            # Show confirmation dialog using GTK4 approach
            dialog = Gtk.MessageDialog(
                transient_for=self.get_root(),
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Kill Process",
                secondary_text=f"Are you sure you want to kill '{process_name}' (PID: {pid})?"
            )
            
            # Connect to response signal
            dialog.connect("response", self._on_kill_dialog_response, pid, process_name)
            dialog.present()
                
        except Exception as e:
            self.logger.error(f"Failed to kill process: {e}")
    
    def _on_kill_dialog_response(self, dialog: Gtk.MessageDialog, response: int, pid: int, process_name: str) -> None:
        """Handle kill dialog response."""
        try:
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                # Kill the process using subprocess for better error handling
                import subprocess
                try:
                    result = subprocess.run(['kill', str(pid)], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        self.logger.info(f"Killed process {process_name} (PID: {pid})")
                        # Show success notification
                        self._show_notification(f"Process {process_name} killed successfully", "success")
                    else:
                        self.logger.error(f"Failed to kill process {process_name} (PID: {pid}): {result.stderr}")
                        self._show_notification(f"Failed to kill process {process_name}", "error")
                except subprocess.TimeoutExpired:
                    self.logger.error(f"Timeout killing process {process_name} (PID: {pid})")
                    self._show_notification(f"Timeout killing process {process_name}", "error")
                except Exception as e:
                    self.logger.error(f"Error killing process {process_name} (PID: {pid}): {e}")
                    self._show_notification(f"Error killing process {process_name}", "error")
                
                # Refresh the process list
                self._update_user_processes_table()
                
        except Exception as e:
            self.logger.error(f"Failed to handle kill dialog response: {e}")
    
    def _show_notification(self, message: str, notification_type: str = "info") -> None:
        """Show a simple notification to the user."""
        try:
            # Create a simple notification dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.get_root(),
                message_type=Gtk.MessageType.INFO if notification_type == "success" else Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=notification_type.title(),
                secondary_text=message
            )
            
            # Auto-close after 3 seconds
            def close_dialog():
                dialog.destroy()
                return False  # Don't repeat
            
            GLib.timeout_add(3000, close_dialog)
            dialog.present()
            
        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")
    
    def _on_sort_changed(self, model: Gtk.TreeStore) -> None:
        """Track sort order changes."""
        try:
            self.current_sort_column = model.get_sort_column_id()[0]
            self.current_sort_order = model.get_sort_column_id()[1]
        except Exception as e:
            self.logger.error(f"Failed to track sort change: {e}")
    
    def _on_selection_changed(self, selection: Gtk.TreeSelection) -> None:
        """Track selected PID when selection changes."""
        try:
            model, treeiter = selection.get_selected()
            if treeiter is not None:
                self.selected_pid = model.get_value(treeiter, 6)  # PID column
            else:
                self.selected_pid = None
        except Exception as e:
            self.logger.error(f"Failed to track selection: {e}")
    
    def _restore_selection(self) -> None:
        """Restore the previously selected PID after refresh."""
        if self.selected_pid is None:
            return
        
        try:
            # Find the row with the previously selected PID
            model = self.process_treeview.get_model()
            treeiter = model.get_iter_first()
            
            while treeiter is not None:
                pid = model.get_value(treeiter, 6)  # PID column
                if pid == self.selected_pid:
                    # Select this row
                    selection = self.process_treeview.get_selection()
                    selection.select_iter(treeiter)
                    # Make sure the row is visible
                    path = model.get_path(treeiter)
                    self.process_treeview.scroll_to_cell(path, None, True, 0.5, 0.5)
                    break
                treeiter = model.iter_next(treeiter)
                
        except Exception as e:
            self.logger.error(f"Failed to restore selection: {e}")
    
    def _create_process_list(self) -> Gtk.Box:
        """Create the process list section."""
        process_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        process_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="Top Processes")
        title_label.add_css_class("title-2")
        process_box.append(title_label)
        
        # Process list
        self.process_listbox = Gtk.ListBox()
        self.process_listbox.add_css_class("process-list")
        process_box.append(self.process_listbox)
        
        return process_box
    
    def _setup_update_timer(self) -> None:
        """Setup the update timer for real-time monitoring."""
        # Update immediately
        self._update_metrics()
        
        # Set up timer for periodic updates (every 1000ms to sync with graph updates)
        self._update_timer_id = GLib.timeout_add(1000, self._update_metrics)
    
    def _update_metrics(self) -> bool:
        """Update all metrics and return True to continue the timer."""
        try:
            # Update system health
            # Update CPU metrics
            self._update_cpu_metrics()
            
            # Update memory metrics
            self._update_memory_metrics()
            
            # Update disk metrics
            self._update_disk_metrics()
            
            # Update network metrics
            self._update_network_metrics()
            
            # Update process list less frequently to reduce load
            if not hasattr(self, '_process_update_counter'):
                self._process_update_counter = 0
            self._process_update_counter += 1
            
            # Only update process list every 3 updates (every 9 seconds)
            if self._process_update_counter >= 3:
                self._update_process_list()
                self._update_user_processes_table()
                self._process_update_counter = 0
            
            # Update last updated timestamp
            now = datetime.now().strftime("%H:%M:%S")
            self.last_updated_label.set_label(f"Last updated: {now}")
            
            return True  # Continue the timer
            
        except Exception as e:
            self.logger.error(f"Failed to update metrics: {e}")
            return True  # Continue the timer even on error
    
    def _update_health_score(self) -> None:
        """Update the system health score."""
        try:
            health_score = self.system_monitor.get_system_health_score()
            
            # Update label
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
            
            self.health_score_label.set_label(f"System Health: {status} ({health_score:.0f}/100)")
            
            # Update progress bar
            self.health_bar.set_fraction(health_score / 100.0)
            
            # Update CSS class
            self.health_score_label.remove_css_class("health-excellent")
            self.health_score_label.remove_css_class("health-good")
            self.health_score_label.remove_css_class("health-fair")
            self.health_score_label.remove_css_class("health-poor")
            self.health_score_label.add_css_class(css_class)
            
        except Exception as e:
            self.logger.error(f"Failed to update health score: {e}")
    
    def _update_cpu_metrics(self) -> None:
        """Update CPU metrics."""
        try:
            cpu_info = self.system_monitor.get_cpu_info()
            
            # Update CPU usage label
            cpu_usage_text = f"CPU Usage: {cpu_info.usage_percent:.1f}%"
            self.cpu_usage_label.set_label(cpu_usage_text)
            
            # Update CPU model info
            cpu_model_text = f"{cpu_info.model_name}"
            self.cpu_model_label.set_label(cpu_model_text)
            
            # Update CPU architecture and cache info
            self.cpu_arch_label.set_label(f"Architecture: {cpu_info.architecture}")
            
            # Try to get cache info from CPU info using existing system monitor
            try:
                cpu_cache_info = self.system_monitor._cpu_info_cache
                if cpu_cache_info:
                    l2_cache = cpu_cache_info.get('l2_cache_size', 'Unknown')
                    l3_cache = cpu_cache_info.get('l3_cache_size', 'Unknown')
                    
                    # Format L3 cache if it's a raw number
                    if isinstance(l3_cache, (int, str)) and str(l3_cache).isdigit():
                        l3_bytes = int(l3_cache)
                        if l3_bytes >= 1024**3:  # GB
                            l3_formatted = f"{l3_bytes / (1024**3):.1f} GiB"
                        elif l3_bytes >= 1024**2:  # MB
                            l3_formatted = f"{l3_bytes / (1024**2):.1f} MiB"
                        else:
                            l3_formatted = f"{l3_bytes} B"
                    else:
                        l3_formatted = str(l3_cache)
                    
                    cache_text = f"L2: {l2_cache}, L3: {l3_formatted}"
                else:
                    cache_text = "Cache: Unknown"
            except:
                cache_text = "Cache: Unknown"
            
            self.cpu_cache_label.set_label(cache_text)
            
            # Detailed CPU information removed - only showing main info now
            
            # Update detailed CPU specifications
            self.cpu_speed_label.set_label(f"{cpu_info.frequency_mhz:.0f} MHz")
            
            # Fix base frequency display - convert to GHz if it's in MHz
            if cpu_info.base_frequency_mhz >= 1000:
                base_freq_text = f"{cpu_info.base_frequency_mhz/1000:.1f} GHz"
            else:
                base_freq_text = f"{cpu_info.base_frequency_mhz:.0f} MHz"
            self.cpu_base_speed_label.set_label(base_freq_text)
            
            self.sockets_label.set_label(str(cpu_info.socket_count))
            self.physical_cores_label.set_label(str(cpu_info.core_count))
            self.logical_processors_label.set_label(str(cpu_info.logical_processor_count))
            self.process_count_label.set_label(str(cpu_info.process_count))
            self.thread_count_label.set_label(str(cpu_info.thread_count))
            self.zombie_processes_label.set_label(str(cpu_info.zombie_process_count))
            
            # Format uptime
            uptime_hours = int(cpu_info.uptime_seconds // 3600)
            uptime_minutes = int((cpu_info.uptime_seconds % 3600) // 60)
            uptime_seconds = int(cpu_info.uptime_seconds % 60)
            uptime_text = f"{uptime_hours:02d}:{uptime_minutes:02d}:{uptime_seconds:02d}"
            self.uptime_label.set_label(uptime_text)
            
            # Update virtualization status
            virtualization_text = "Enabled" if cpu_info.virtualization_enabled else "Disabled"
            self.virtualization_label.set_label(virtualization_text)
            
            # Update multi-core chart
            if self.cpu_chart and hasattr(cpu_info, 'core_usage'):
                # Ensure all cores are represented, even with 0% usage
                for core_id in range(cpu_info.logical_processor_count):
                    if core_id < len(cpu_info.core_usage):
                        core_usage = cpu_info.core_usage[core_id]
                    else:
                        core_usage = 0.0  # Default to 0% if core data is missing
                    self.cpu_chart.add_core_data(core_id, core_usage)
            
            # Store in history
            self.cpu_history.append(cpu_info.usage_percent)
            if len(self.cpu_history) > self.max_history_points:
                self.cpu_history.pop(0)
            
        except Exception as e:
            self.logger.error(f"Failed to update CPU metrics: {e}")
    
    def _update_memory_metrics(self) -> None:
        """Update memory metrics."""
        try:
            memory_info = self.system_monitor.get_memory_info()
            
            # Update memory usage label
            memory_usage_text = f"Memory Usage: {memory_info.used_gb:.1f} GB / {memory_info.total_gb:.1f} GB"
            self.memory_usage_label.set_label(memory_usage_text)
            
            # Update memory percentage label
            memory_percent_text = f"Usage: {memory_info.usage_percent:.1f}%"
            self.memory_percent_label.set_label(memory_percent_text)
            
            # Update swap usage label
            if memory_info.swap_total_gb > 0.1:  # Check for meaningful swap size
                swap_text = f"Swap: {memory_info.swap_used_gb:.1f} GB / {memory_info.swap_total_gb:.1f} GB ({memory_info.swap_usage_percent:.1f}%)"
            else:
                swap_text = "Swap: No swap detected"
            self.swap_usage_label.set_label(swap_text)
            
            # Update chart
            if self.memory_chart:
                self.memory_chart.add_data_point(memory_info.usage_percent)
            
            # Store in history
            self.memory_history.append(memory_info.usage_percent)
            if len(self.memory_history) > self.max_history_points:
                self.memory_history.pop(0)
            
        except Exception as e:
            self.logger.error(f"Failed to update memory metrics: {e}")
    
    def _update_disk_metrics(self) -> None:
        """Update disk metrics."""
        try:
            disk_info_list = self.system_monitor.get_disk_info()
            
            if disk_info_list:
                # Use the first disk (usually the root filesystem)
                disk_info = disk_info_list[0]
                
                # Update disk usage label
                disk_usage_text = f"Disk Usage: {disk_info.used_gb:.1f} GB / {disk_info.total_gb:.1f} GB"
                self.disk_usage_label.set_label(disk_usage_text)
                
                # Update disk percentage label
                disk_percent_text = f"Usage: {disk_info.usage_percent:.1f}%"
                self.disk_percent_label.set_label(disk_percent_text)
                
                # Update chart with separate read and write IOPS
                if self.disk_chart:
                    self.disk_chart.add_data_point(disk_info.read_iops, "Read")
                    self.disk_chart.add_data_point(disk_info.write_iops, "Write")
                
                # Update disk partitions
                self._update_disk_partitions(disk_info_list)
            
        except Exception as e:
            self.logger.error(f"Failed to update disk metrics: {e}")
    
    def _update_disk_partitions(self, disk_info_list) -> None:
        """Update disk partitions display in two columns."""
        try:
            # Clear existing partition items
            while self.partitions_container.get_first_child():
                self.partitions_container.remove(self.partitions_container.get_first_child())
            
            # Add partition items in two columns
            for i, disk_info in enumerate(disk_info_list):
                partition_item = self._create_partition_item(
                    disk_info.device,
                    disk_info.mountpoint,
                    disk_info.used_gb,
                    disk_info.total_gb,
                    disk_info.usage_percent
                )
                
                # Calculate grid position (2 columns)
                row = i // 2
                col = i % 2
                self.partitions_container.attach(partition_item, col, row, 1, 1)
                
        except Exception as e:
            self.logger.error(f"Failed to update disk partitions: {e}")
    
    def _update_network_metrics(self) -> None:
        """Update network metrics and individual interface charts."""
        try:
            network_info_list = self.system_monitor.get_network_info()
            
            if network_info_list:
                # Calculate total speed across all active interfaces
                total_in_speed = 0.0
                total_out_speed = 0.0
                active_interfaces = 0
                
                for network_info in network_info_list:
                    # Only count interfaces that are actually active
                    if (network_info.ip_address != "N/A" and 
                        (network_info.in_speed_mbps > 0.0 or network_info.out_speed_mbps > 0.0 or
                         network_info.bytes_sent > 0 or network_info.bytes_recv > 0)):
                        
                        total_in_speed += network_info.in_speed_mbps
                        total_out_speed += network_info.out_speed_mbps
                        active_interfaces += 1
                
                # Calculate total speed
                total_speed = total_in_speed + total_out_speed
                
                # Auto-scale speed units
                speed_text = self._format_network_speed(total_speed)
                self.network_speed_label.set_label(speed_text)
                
                # Update individual interface charts
                self._update_interface_charts(network_info_list)
            
        except Exception as e:
            self.logger.error(f"Failed to update network metrics: {e}")
    
    def _format_network_speed(self, speed_mbps: float) -> str:
        """Format network speed with auto-scaling units."""
        try:
            if speed_mbps >= 1000.0:
                # Convert to Gbps
                speed_gbps = speed_mbps / 1000.0
                return f"{speed_gbps:.3f} Gbps"
            elif speed_mbps >= 1.0:
                # Keep as Mbps
                return f"{speed_mbps:.3f} Mbps"
            else:
                # Convert to kbps
                speed_kbps = speed_mbps * 1000.0
                return f"{speed_kbps:.1f} kbps"
        except Exception as e:
            self.logger.error(f"Error formatting network speed: {e}")
            return "0.000 Mbps"
    
    def _update_interface_charts(self, network_info_list) -> None:
        """Update or create individual interface charts."""
        try:
            # Get current interface names
            current_interfaces = {info.interface for info in network_info_list}
            
            # Get all known interfaces (both active and disconnected)
            all_known_interfaces = set(self.network_interface_charts.keys()) | set(self.disconnected_interface_widgets.keys())
            
            # Remove charts for interfaces that no longer exist
            interfaces_to_remove = []
            for interface_name in all_known_interfaces:
                if interface_name not in current_interfaces:
                    interfaces_to_remove.append(interface_name)
            
            for interface_name in interfaces_to_remove:
                # Remove active chart if exists
                if interface_name in self.network_interface_charts:
                    chart = self.network_interface_charts[interface_name]
                    if chart.get_parent():
                        chart.get_parent().remove(chart)
                    chart.cleanup()
                    del self.network_interface_charts[interface_name]
                
                # Remove disconnected widget if exists
                if interface_name in self.disconnected_interface_widgets:
                    widget = self.disconnected_interface_widgets[interface_name]
                    if widget.get_parent():
                        widget.get_parent().remove(widget)
                    del self.disconnected_interface_widgets[interface_name]
            
            # Check for disconnected interfaces (interfaces that exist but have no activity)
            disconnected_interfaces = set()
            for network_info in network_info_list:
                interface_name = network_info.interface
                # Consider interface disconnected if it has no IP address or no activity
                if (network_info.ip_address == "N/A" or 
                    (network_info.in_speed_mbps == 0.0 and network_info.out_speed_mbps == 0.0 and 
                     network_info.bytes_sent == 0 and network_info.bytes_recv == 0)):
                    disconnected_interfaces.add(interface_name)
            
            # Create or update charts for current interfaces
            for network_info in network_info_list:
                interface_name = network_info.interface
                
                # Skip if interface is disconnected
                if interface_name in disconnected_interfaces:
                    # Remove chart if it exists
                    if interface_name in self.network_interface_charts:
                        chart = self.network_interface_charts[interface_name]
                        if chart.get_parent():
                            chart.get_parent().remove(chart)
                        chart.cleanup()
                        del self.network_interface_charts[interface_name]
                    
                    # Create disconnected widget if it doesn't exist
                    if interface_name not in self.disconnected_interface_widgets:
                        # Remove placeholder if it exists
                        first_child = self.network_charts_container.get_first_child()
                        if first_child and isinstance(first_child, Gtk.Label) and "Loading" in first_child.get_label():
                            self.network_charts_container.remove(first_child)
                        
                        # Create disconnected widget
                        widget = DisconnectedInterfaceWidget(interface_name)
                        self.network_charts_container.append(widget)
                        self.disconnected_interface_widgets[interface_name] = widget
                        
                        self.logger.info(f"Created disconnected widget for interface: {interface_name}")
                    
                    continue
                
                # Remove disconnected widget if interface is now active
                if interface_name in self.disconnected_interface_widgets:
                    widget = self.disconnected_interface_widgets[interface_name]
                    if widget.get_parent():
                        widget.get_parent().remove(widget)
                    del self.disconnected_interface_widgets[interface_name]
                
                # Create new chart if it doesn't exist
                if interface_name not in self.network_interface_charts:
                    # Remove placeholder if it exists
                    first_child = self.network_charts_container.get_first_child()
                    if first_child and isinstance(first_child, Gtk.Label) and "Loading" in first_child.get_label():
                        self.network_charts_container.remove(first_child)
                    
                    # Create new chart
                    chart = NetworkInterfaceChartWidget(interface_name, max_points=30)
                    chart.set_size_request(600, 300)
                    chart.add_css_class("network-interface-chart")
                    
                    # Add to container
                    self.network_charts_container.append(chart)
                    self.network_interface_charts[interface_name] = chart
                    
                    self.logger.info(f"Created chart for interface: {interface_name}")
                
                # Update chart with current data
                chart = self.network_interface_charts[interface_name]
                chart.add_data(network_info.in_speed_mbps, network_info.out_speed_mbps)
                

            
        except Exception as e:
            self.logger.error(f"Failed to update interface charts: {e}")
    
    def _update_process_list(self) -> None:
        """Update the top process list."""
        try:
            # Clear existing processes
            while self.process_listbox.get_first_child():
                self.process_listbox.remove(self.process_listbox.get_first_child())
            
            # Get top processes
            processes = self.system_monitor.get_top_processes(limit=5)
            
            for process in processes:
                # Create process row
                row = Gtk.ListBoxRow()
                
                # Process info box
                info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                info_box.set_margin_start(8)
                info_box.set_margin_end(8)
                info_box.set_margin_top(4)
                info_box.set_margin_bottom(4)
                
                # Process name and PID
                name_label = Gtk.Label(label=f"{process.name} (PID: {process.pid})")
                name_label.set_hexpand(True)
                name_label.set_xalign(0)
                info_box.append(name_label)
                
                # CPU usage
                cpu_label = Gtk.Label(label=f"CPU: {process.cpu_percent:.1f}%")
                info_box.append(cpu_label)
                
                # Memory usage
                memory_label = Gtk.Label(label=f"RAM: {process.memory_mb:.1f} MB")
                info_box.append(memory_label)
                
                row.set_child(info_box)
                self.process_listbox.append(row)
            
        except Exception as e:
            self.logger.error(f"Failed to update process list: {e}")
    
    def _update_user_processes_table(self) -> None:
        """Update the user processes table."""
        try:
            # Store current selection and sort order before clearing
            current_selection = self.selected_pid
            current_sort_column = self.current_sort_column
            current_sort_order = self.current_sort_order

            # Save scroll position
            scroll_value = None
            if hasattr(self, 'process_treeview_scrolled_window'):
                vadjustment = self.process_treeview_scrolled_window.get_vadjustment()
                if vadjustment:
                    scroll_value = vadjustment.get_value()

            # Clear existing data
            self.process_store.clear()
            
            # Get user processes
            processes = self.system_monitor.get_user_processes(limit=50)
            
            for process in processes:
                # Format data for display
                memory_text = self._format_memory(process.memory_mb)
                disk_read_total = self._format_disk_io(process.disk_read_total_mb)
                disk_write_total = self._format_disk_io(process.disk_write_total_mb)
                disk_read_rate = "N/A"  # TODO: Implement rate calculation
                disk_write_rate = "N/A"  # TODO: Implement rate calculation
                priority_text = self._format_priority(process.priority)
                
                # Add to tree store
                self.process_store.append(None, [
                    process.name,                    # Process Name
                    process.username,                # User
                    f"{process.cpu_percent:.2f}%",   # % CPU
                    str(process.pid),                # ID
                    memory_text,                     # Memory
                    self._format_disk_io(process.disk_read_total_mb),  # Disk Read
                    self._format_disk_io(process.disk_write_total_mb), # Disk Write
                    priority_text,                   # Priority
                    process.pid                      # PID (hidden, for kill functionality)
                ])
            
            # Restore sort order after refresh
            self.process_store.set_sort_column_id(current_sort_column, current_sort_order)
            
            # Restore selection after refresh
            if current_selection is not None:
                self.selected_pid = current_selection
                self._restore_selection()

            # Restore scroll position
            if scroll_value is not None and hasattr(self, 'process_treeview_scrolled_window'):
                vadjustment = self.process_treeview_scrolled_window.get_vadjustment()
                if vadjustment:
                    GLib.idle_add(vadjustment.set_value, scroll_value)

        except Exception as e:
            self.logger.error(f"Failed to update user processes table: {e}")
    
    def _format_memory(self, memory_mb: float) -> str:
        """Format memory usage with appropriate units."""
        if memory_mb >= 1024:
            return f"{memory_mb/1024:.1f} MB"
        else:
            return f"{memory_mb:.1f} kB"
    
    def _format_disk_io(self, io_mb: float) -> str:
        """Format disk I/O with appropriate units."""
        if io_mb >= 1024:
            return f"{io_mb/1024:.1f} GB"
        elif io_mb >= 1:
            return f"{io_mb:.1f} MB"
        else:
            return f"{io_mb*1024:.1f} kB"
    
    def _format_priority(self, priority: int) -> str:
        """Format process priority."""
        if priority < 0:
            return "High"
        elif priority > 0:
            return "Low"
        else:
            return "Normal"
    
    # Sorting functions for tree store
    def _sort_string_column(self, model, iter1, iter2, column_id):
        """Sort string columns alphabetically."""
        val1 = model.get_value(iter1, column_id)
        val2 = model.get_value(iter2, column_id)
        
        # Handle case-insensitive sorting for process names
        if column_id == 0:  # Process Name column
            val1 = val1.lower()
            val2 = val2.lower()
        
        if val1 < val2:
            return -1
        elif val1 > val2:
            return 1
        return 0
    
    def _sort_cpu_column(self, model, iter1, iter2, column_id):
        """Sort CPU percentage column numerically."""
        val1 = model.get_value(iter1, column_id)
        val2 = model.get_value(iter2, column_id)
        # Extract numeric value from "X.XX%" format
        try:
            cpu1 = float(val1.replace('%', ''))
            cpu2 = float(val2.replace('%', ''))
            return cpu1 - cpu2
        except ValueError:
            return 0
    
    def _sort_pid_column(self, model, iter1, iter2, column_id):
        """Sort PID column numerically."""
        val1 = model.get_value(iter1, column_id)
        val2 = model.get_value(iter2, column_id)
        try:
            pid1 = int(val1)
            pid2 = int(val2)
            return pid1 - pid2
        except ValueError:
            return 0
    
    def _sort_memory_column(self, model, iter1, iter2, column_id):
        """Sort memory column by converting to MB for comparison."""
        val1 = model.get_value(iter1, column_id)
        val2 = model.get_value(iter2, column_id)
        
        def parse_memory(mem_str):
            """Parse memory string to MB."""
            try:
                if 'GB' in mem_str:
                    return float(mem_str.replace(' MB', '')) * 1024
                elif 'MB' in mem_str:
                    return float(mem_str.replace(' MB', ''))
                elif 'kB' in mem_str:
                    return float(mem_str.replace(' kB', '')) / 1024
                else:
                    return 0.0
            except ValueError:
                return 0.0
        
        mem1 = parse_memory(val1)
        mem2 = parse_memory(val2)
        return mem1 - mem2
    
    def _sort_disk_column(self, model, iter1, iter2, column_id):
        """Sort disk columns by converting to MB for comparison."""
        val1 = model.get_value(iter1, column_id)
        val2 = model.get_value(iter2, column_id)
        def parse_disk_io(io_str):
            if io_str.endswith("GB"):
                return float(io_str.replace("GB", "").strip()) * 1024
            elif io_str.endswith("MB"):
                return float(io_str.replace("MB", "").strip())
            elif io_str.endswith("kB"):
                return float(io_str.replace("kB", "").strip()) / 1024
            else:
                return 0.0
        disk1 = parse_disk_io(val1)
        disk2 = parse_disk_io(val2)
        return (disk1 > disk2) - (disk1 < disk2)
    
    def _sort_priority_column(self, model, iter1, iter2, column_id):
        """Sort priority column by priority level."""
        val1 = model.get_value(iter1, column_id)
        val2 = model.get_value(iter2, column_id)
        
        # Priority order: High (0), Normal (1), Low (2)
        priority_order = {"High": 0, "Normal": 1, "Low": 2}
        
        order1 = priority_order.get(val1, 1)
        order2 = priority_order.get(val2, 1)
        
        return order1 - order2
    
    def _on_process_treeview_right_click(self, gesture, n_press, x, y):
        if n_press == 1 and gesture.get_current_button() == 3:  # Right-click
            treeview = self.process_treeview
            path_info = treeview.get_path_at_pos(int(x), int(y))
            if path_info is not None:
                path, col, cell_x, cell_y = path_info
                model = treeview.get_model()
                treeiter = model.get_iter(path)
                if treeiter is not None:
                    pid = model.get_value(treeiter, 8)
                    process_name = model.get_value(treeiter, 0)
                    menu = Gtk.Menu()
                    kill_item = Gtk.MenuItem(label="Kill Process")
                    kill_item.connect("activate", self._on_kill_menu_activate, pid, process_name)
                    menu.append(kill_item)
                    # Add more menu items here in the future
                    menu.show_all()
                    menu.popup_at_pointer(None)
                    return True
        return False

    def _on_kill_menu_activate(self, menuitem, pid, process_name):
        try:
            dialog = Gtk.MessageDialog(
                transient_for=self.get_root(),
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Kill Process",
                secondary_text=f"Are you sure you want to kill '{process_name}' (PID: {pid})?"
            )
            dialog.connect("response", self._on_kill_dialog_response, pid, process_name)
            dialog.present()
        except Exception as e:
            self.logger.error(f"Failed to show kill dialog from menu: {e}")

    
    def cleanup(self) -> None:
        """Clean up resources to prevent memory leaks."""
        try:
            # Remove the update timer
            if hasattr(self, '_update_timer_id') and self._update_timer_id:
                GLib.source_remove(self._update_timer_id)
                self._update_timer_id = None
            
            # Clean up charts
            if hasattr(self, 'cpu_chart') and self.cpu_chart:
                self.cpu_chart.cleanup()
            if hasattr(self, 'memory_chart') and self.memory_chart:
                self.memory_chart.cleanup()
            if hasattr(self, 'disk_chart') and self.disk_chart:
                self.disk_chart.cleanup()
            if hasattr(self, 'network_chart') and self.network_chart:
                self.network_chart.cleanup()
            
            # Clean up individual network interface charts
            if hasattr(self, 'network_interface_charts'):
                for chart in self.network_interface_charts.values():
                    chart.cleanup()
                self.network_interface_charts.clear()
            
            # Clean up disconnected interface widgets
            if hasattr(self, 'disconnected_interface_widgets'):
                self.disconnected_interface_widgets.clear()
            
            # Clear history data
            if hasattr(self, 'cpu_history'):
                self.cpu_history.clear()
            if hasattr(self, 'memory_history'):
                self.memory_history.clear()
            
            # Reset counters
            if hasattr(self, '_process_update_counter'):
                self._process_update_counter = 0
            
            # Force garbage collection
            import gc
            gc.collect()
            
            self.logger.info("Dashboard widget cleaned up")
        except Exception as e:
            self.logger.error(f"Error during dashboard cleanup: {e}") 