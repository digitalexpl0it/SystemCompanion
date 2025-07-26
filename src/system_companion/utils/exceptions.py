"""
Custom exceptions for System Companion.

This module defines application-specific exceptions for better error handling.
"""

from typing import Optional


class SystemCompanionError(Exception):
    """Base exception for System Companion application."""
    
    def __init__(self, message: str, details: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class SystemMonitorError(SystemCompanionError):
    """Exception raised when system monitoring fails."""
    pass


class MonitoringError(SystemCompanionError):
    """Exception raised when system monitoring fails."""
    pass


class PerformanceAnalysisError(SystemCompanionError):
    """Exception raised when performance analysis fails."""
    pass


class MaintenanceError(SystemCompanionError):
    """Exception raised when maintenance operations fail."""
    pass


class DatabaseError(SystemCompanionError):
    """Exception raised when database operations fail."""
    pass


class ConfigurationError(SystemCompanionError):
    """Exception raised when configuration operations fail."""
    pass


class PermissionError(SystemCompanionError):
    """Exception raised when insufficient permissions are detected."""
    pass


class HardwareError(SystemCompanionError):
    """Exception raised when hardware monitoring fails."""
    pass


class NetworkError(SystemCompanionError):
    """Exception raised when network operations fail."""
    pass


class UIError(SystemCompanionError):
    """Exception raised when UI operations fail."""
    pass


class ValidationError(SystemCompanionError):
    """Exception raised when data validation fails."""
    pass 