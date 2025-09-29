"""Configuration management for DEX monitoring system."""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager for the DEX monitoring system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to configuration file. Defaults to config/config.yaml
        """
        if config_path is None:
            # Default to config/config.yaml relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            config_path = project_root / "config" / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'database.type')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self.get('database', {})
    
    @property
    def blockchain_config(self) -> Dict[str, Any]:
        """Get blockchain configuration."""
        return self.get('blockchain', {})
    
    @property
    def market_data_config(self) -> Dict[str, Any]:
        """Get market data configuration."""
        return self.get('market_data', {})
    
    @property
    def alerts_config(self) -> Dict[str, Any]:
        """Get alerts configuration."""
        return self.get('alerts', {})
    
    @property
    def dashboard_config(self) -> Dict[str, Any]:
        """Get dashboard configuration."""
        return self.get('dashboard', {})
    
    @property
    def monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return self.get('monitoring', {})
    
    @property
    def simulation_config(self) -> Dict[str, Any]:
        """Get simulation configuration."""
        return self.get('simulation', {})


# Global configuration instance
config = Config()