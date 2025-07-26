"""
UI widgets for System Companion.

This package contains reusable UI widgets for the application.
"""

from .dashboard_widget import DashboardWidget
from .performance_widget import PerformanceWidget
from .health_widget import HealthWidget
from .maintenance_widget import MaintenanceWidget
from .security_widget import SecurityWidget
from .settings_widget import SettingsWidget
from .multi_interface_chart_widget import MultiInterfaceChartWidget
from .network_interface_chart_widget import NetworkInterfaceChartWidget
from .disconnected_interface_widget import DisconnectedInterfaceWidget

__all__ = ['DashboardWidget', 'PerformanceWidget', 'HealthWidget', 'MaintenanceWidget', 'SecurityWidget', 'SettingsWidget', 'MultiInterfaceChartWidget', 'NetworkInterfaceChartWidget', 'DisconnectedInterfaceWidget'] 