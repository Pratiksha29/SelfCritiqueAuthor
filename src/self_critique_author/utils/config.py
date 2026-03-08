"""Configuration management for the application."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Application configuration."""
    name: str
    version: str
    debug: bool = False


@dataclass
class LLMConfig:
    """LLM configuration."""
    provider: str = "gemini"
    model: str = "gemini-1.5-flash"
    max_retries: int = 3
    delay_seconds: int = 5
    api_key: Optional[str] = None


@dataclass
class StorageConfig:
    """Storage configuration."""
    default_format: str = "json"
    output_directory: str = "data/processed"
    grievance_directory: str = "data/processed/grievances"
    message_directory: str = "data/processed/messages"


@dataclass
class VerificationConfig:
    """Verification configuration."""
    whatsapp_enabled: bool = True
    doctor_enabled: bool = True
    message_format: str = "professional"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "structured"
    file: str = "logs/app.log"


class Config:
    """Main configuration manager."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config_data = self._load_config()
        
        # Initialize configuration objects
        self.app = AppConfig(**self._config_data.get("app", {}))
        self.llm = LLMConfig(**self._config_data.get("llm", {}))
        self.storage = StorageConfig(**self._config_data.get("storage", {}))
        self.verification = VerificationConfig(**self._config_data.get("verification", {}))
        self.logging = LoggingConfig(**self._config_data.get("logging", {}))
        
        # Override with environment variables
        self._load_env_overrides()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        # Try multiple locations
        paths = [
            "config/settings.yaml",
            "../config/settings.yaml",
            "../../config/settings.yaml",
        ]
        
        for path in paths:
            if Path(path).exists():
                return path
        
        # Fallback to first path
        return paths[0]
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Warning: Config file {self.config_path} not found, using defaults")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            return {}
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables."""
        # LLM configuration
        if os.getenv("GEMINI_API_KEY"):
            self.llm.api_key = os.getenv("GEMINI_API_KEY")
        
        if os.getenv("LLM_PROVIDER"):
            self.llm.provider = os.getenv("LLM_PROVIDER")
        
        if os.getenv("LLM_MODEL"):
            self.llm.model = os.getenv("LLM_MODEL")
        
        # Storage configuration
        if os.getenv("OUTPUT_DIRECTORY"):
            self.storage.output_directory = os.getenv("OUTPUT_DIRECTORY")
        
        # Verification configuration
        if os.getenv("WHATSAPP_ENABLED"):
            self.verification.whatsapp_enabled = os.getenv("WHATSAPP_ENABLED").lower() == "true"
        
        if os.getenv("DOCTOR_ENABLED"):
            self.verification.doctor_enabled = os.getenv("DOCTOR_ENABLED").lower() == "true"
        
        # Logging configuration
        if os.getenv("LOG_LEVEL"):
            self.logging.level = os.getenv("LOG_LEVEL")
        
        if os.getenv("DEBUG"):
            self.app.debug = os.getenv("DEBUG").lower() == "true"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split('.')
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def reload(self):
        """Reload configuration from file."""
        self._config_data = self._load_config()
        self._load_env_overrides()


# Global configuration instance
config = Config()
