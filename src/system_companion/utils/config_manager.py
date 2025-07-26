"""
Configuration manager for System Companion.

This module provides configuration management functionality
for storing and retrieving application settings.
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Manages application configuration and settings."""
    
    def __init__(self) -> None:
        """Initialize the configuration manager."""
        self.logger = logging.getLogger("system_companion.utils.config_manager")
        
        # Default configuration
        self.default_config = {
            # General settings
            'autostart': False,
            
            # Notification settings
            'notifications_enabled': True,
            'critical_notifications': True,
            'performance_notifications': True,
            'security_notifications': True,
            
            # Advanced settings
            'debug_mode': False,
            'log_level': 'INFO',
            'data_retention_days': 30
        }
        
        # Configuration file path
        self.config_dir = Path.home() / '.config' / 'system-companion'
        self.config_file = self.config_dir / 'config.json'
        
        # Current configuration
        self.config = self.default_config.copy()
        
        # Load configuration
        self._load_config()
        
        self.logger.info("Configuration manager initialized")
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                
                # Merge with default config (preserve defaults for missing keys)
                self.config.update(loaded_config)
                self.logger.info(f"Configuration loaded from {self.config_file}")
            else:
                # Create config directory if it doesn't exist
                self.config_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info("No configuration file found, using defaults")
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Keep using default configuration
    
    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return self.config.copy()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value."""
        return self.config.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set a specific setting value."""
        self.config[key] = value
        self.logger.debug(f"Setting '{key}' updated to: {value}")
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        self.config.update(new_config)
        self.logger.debug("Configuration updated")
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.config = self.default_config.copy()
        self.logger.info("Configuration reset to defaults")
    
    def get_config_file_path(self) -> Path:
        """Get the configuration file path."""
        return self.config_file
    
    def get_config_dir_path(self) -> Path:
        """Get the configuration directory path."""
        return self.config_dir
    
    def is_first_run(self) -> bool:
        """Check if this is the first run of the application."""
        return not self.config_file.exists()
    
    def export_config(self, file_path: Path) -> None:
        """Export configuration to a file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self.logger.info(f"Configuration exported to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            raise
    
    def import_config(self, file_path: Path) -> None:
        """Import configuration from a file."""
        try:
            with open(file_path, 'r') as f:
                imported_config = json.load(f)
            
            # Validate imported config
            if isinstance(imported_config, dict):
                self.config.update(imported_config)
                self.logger.info(f"Configuration imported from {file_path}")
            else:
                raise ValueError("Invalid configuration format")
                
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            raise 