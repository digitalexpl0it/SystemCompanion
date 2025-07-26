"""
System Companion - A fast, optimized, and beautiful system health & maintenance dashboard.

This package provides comprehensive system monitoring, predictive maintenance,
and optimization tools for Ubuntu Linux with a modern GTK4 interface.
"""

__version__ = "0.1.0"
__author__ = "System Companion Team"
__email__ = "team@systemcompanion.dev"

from .core.system_monitor import SystemMonitor
from .core.performance_analyzer import PerformanceAnalyzer
from .core.maintenance_manager import MaintenanceManager
from .ui.main_window import MainWindow
from .data.database import Database

__all__ = [
    "SystemMonitor",
    "PerformanceAnalyzer", 
    "MaintenanceManager",
    "MainWindow",
    "Database",
] 