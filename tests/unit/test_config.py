"""
Tests for configuration management.

This module tests the configuration system functionality.
"""

import pytest
import tempfile
from pathlib import Path

from system_companion.utils.config import Config, SystemCompanionConfig
from system_companion.utils.exceptions import ConfigurationError


class TestSystemCompanionConfig:
    """Test SystemCompanionConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = SystemCompanionConfig()
        
        assert config.window_width == 1200
        assert config.window_height == 800
        assert config.theme == "auto"
        assert config.refresh_interval == 1000
        assert config.enable_cpu_monitoring is True
        assert config.enable_memory_monitoring is True


class TestConfig:
    """Test Config class."""
    
    def test_init_with_default_path(self):
        """Test Config initialization with default path."""
        config = Config()
        assert "system-companion" in str(config.config_file)
    
    def test_init_with_custom_path(self):
        """Test Config initialization with custom path."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            config_file = Path(f.name)
        
        try:
            config = Config(config_file)
            assert config.config_file == config_file
        finally:
            config_file.unlink(missing_ok=True)
    
    def test_get_default_value(self):
        """Test getting default configuration values."""
        config = Config()
        assert config.get("window_width") == 1200
        assert config.get("theme") == "auto"
        assert config.get("nonexistent_key", "default") == "default"
    
    def test_set_and_get_value(self):
        """Test setting and getting configuration values."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            config_file = Path(f.name)
        
        try:
            config = Config(config_file)
            
            # Test valid values
            config.set("window_width", 1400)
            assert config.get("window_width") == 1400
            
            config.set("theme", "dark")
            assert config.get("theme") == "dark"
            
        finally:
            config_file.unlink(missing_ok=True)
    
    def test_validation_window_width(self):
        """Test window width validation."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            config_file = Path(f.name)
        
        try:
            config = Config(config_file)
            
            # Test invalid values
            with pytest.raises(ConfigurationError):
                config.set("window_width", 600)  # Too small
            
            with pytest.raises(ConfigurationError):
                config.set("window_width", "invalid")  # Wrong type
            
        finally:
            config_file.unlink(missing_ok=True)
    
    def test_validation_theme(self):
        """Test theme validation."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            config_file = Path(f.name)
        
        try:
            config = Config(config_file)
            
            # Test valid values
            config.set("theme", "light")
            config.set("theme", "dark")
            config.set("theme", "auto")
            
            # Test invalid value
            with pytest.raises(ConfigurationError):
                config.set("theme", "invalid")
            
        finally:
            config_file.unlink(missing_ok=True)
    
    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            config_file = Path(f.name)
        
        try:
            config = Config(config_file)
            
            # Change some values
            config.set("window_width", 1400)
            config.set("theme", "dark")
            
            # Reset to defaults
            config.reset_to_defaults()
            
            # Check values are back to defaults
            assert config.get("window_width") == 1200
            assert config.get("theme") == "auto"
            
        finally:
            config_file.unlink(missing_ok=True)
    
    def test_get_all(self):
        """Test getting all configuration values."""
        config = Config()
        all_config = config.get_all()
        
        assert isinstance(all_config, dict)
        assert "window_width" in all_config
        assert "theme" in all_config
        assert "refresh_interval" in all_config
    
    def test_update_multiple(self):
        """Test updating multiple configuration values."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            config_file = Path(f.name)
        
        try:
            config = Config(config_file)
            
            updates = {
                "window_width": 1400,
                "theme": "dark",
                "refresh_interval": 2000
            }
            
            config.update(updates)
            
            assert config.get("window_width") == 1400
            assert config.get("theme") == "dark"
            assert config.get("refresh_interval") == 2000
            
        finally:
            config_file.unlink(missing_ok=True) 