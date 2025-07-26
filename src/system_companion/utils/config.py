"""
Configuration management for System Companion.

This module handles application configuration with JSON-based settings,
validation, and automatic saving/loading.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, asdict, field

from .exceptions import ConfigurationError


@dataclass
class SystemCompanionConfig:
    """Configuration data class for System Companion."""
    
    # UI Settings
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    theme: str = "auto"  # auto, light, dark
    refresh_interval: int = 1000  # milliseconds
    window_size: dict = None  # Will be set to default if None
    
    # General Settings
    autostart: bool = False
    show_tray_icon: bool = True
    notifications_enabled: bool = True
    critical_notifications: bool = True
    performance_notifications: bool = True
    security_notifications: bool = True
    debug_mode: bool = False
    
    # Performance Settings
    max_history_points: int = 3600  # 1 hour at 1-second intervals
    enable_performance_logging: bool = True
    cache_duration: int = 300  # 5 minutes
    
    # Maintenance Settings
    auto_cleanup_enabled: bool = False
    cleanup_interval_hours: int = 24
    max_log_size_mb: int = 100
    backup_enabled: bool = True
    
    # Notifications
    enable_notifications: bool = True
    notification_timeout: int = 5000  # milliseconds
    critical_threshold_cpu: float = 90.0
    critical_threshold_memory: float = 90.0
    critical_threshold_disk: float = 95.0
    
    # Privacy Settings
    collect_usage_statistics: bool = False
    share_crash_reports: bool = False
    telemetry_enabled: bool = False
    
    # Logging Settings
    log_level: str = "INFO"
    
    # Data Settings
    data_retention_days: int = 30


class Config:
    """Configuration manager for System Companion."""
    
    def __init__(self, config_file: Optional[Path] = None) -> None:
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (default: ~/.config/system-companion/config.json)
        """
        self.logger = logging.getLogger("system_companion.config")
        
        if config_file is None:
            config_dir = Path.home() / ".config" / "system-companion"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file = config_dir / "config.json"
        
        self.config_file = config_file
        self._config = SystemCompanionConfig()
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._config = SystemCompanionConfig(**data)
                self.logger.info(f"Configuration loaded from {self.config_file}")
            else:
                self.logger.info("No configuration file found, using defaults")
                self._save_config()
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Continue with default configuration
            self._config = SystemCompanionConfig()
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self._config), f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        return getattr(self._config, key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            
        Raises:
            ConfigurationError: If key is invalid or value is invalid
        """
        if not hasattr(self._config, key):
            raise ConfigurationError(f"Invalid configuration key: {key}")
        
        # Validate value based on key
        self._validate_value(key, value)
        
        setattr(self._config, key, value)
        self._save_config()
        self.logger.debug(f"Configuration updated: {key} = {value}")
    
    def _validate_value(self, key: str, value: Any) -> None:
        """
        Validate configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            
        Raises:
            ConfigurationError: If value is invalid
        """
        if key == "refresh_interval" and (not isinstance(value, int) or value < 100):
            raise ConfigurationError("Refresh interval must be >= 100ms")
        
        elif key == "window_width" and (not isinstance(value, int) or value < 800):
            raise ConfigurationError("Window width must be >= 800")
        
        elif key == "window_height" and (not isinstance(value, int) or value < 600):
            raise ConfigurationError("Window height must be >= 600")
        
        elif key == "theme" and value not in ["auto", "light", "dark"]:
            raise ConfigurationError("Theme must be 'auto', 'light', or 'dark'")
        
        elif key == "max_history_points" and (not isinstance(value, int) or value < 100):
            raise ConfigurationError("Max history points must be >= 100")
        
        elif key == "critical_threshold_cpu" and (not isinstance(value, (int, float)) or value < 0 or value > 100):
            raise ConfigurationError("CPU threshold must be between 0 and 100")
        
        elif key == "critical_threshold_memory" and (not isinstance(value, (int, float)) or value < 0 or value > 100):
            raise ConfigurationError("Memory threshold must be between 0 and 100")
        
        elif key == "critical_threshold_disk" and (not isinstance(value, (int, float)) or value < 0 or value > 100):
            raise ConfigurationError("Disk threshold must be between 0 and 100")
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config = SystemCompanionConfig()
        self._save_config()
        self.logger.info("Configuration reset to defaults")
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            Dictionary of all configuration values
        """
        return asdict(self._config)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple configuration values.
        
        Args:
            updates: Dictionary of configuration updates
            
        Raises:
            ConfigurationError: If any value is invalid
        """
        for key, value in updates.items():
            self.set(key, value)
        
        self.logger.info(f"Updated {len(updates)} configuration values")
    
    @property
    def config_dir(self) -> Path:
        """Get configuration directory."""
        return self.config_file.parent
    
    @property
    def data_dir(self) -> Path:
        """Get data directory."""
        return Path.home() / ".local" / "share" / "system-companion"
    
    @property
    def cache_dir(self) -> Path:
        """Get cache directory."""
        return Path.home() / ".cache" / "system-companion" 