"""
Configuration management for the paper-to-slides system.

Handles loading and merging configuration from JSON files and environment variables.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv


class ConfigLoader:
    """
    Singleton configuration loader.

    Loads configuration from JSON files and environment variables,
    with environment variables taking precedence.
    """

    _instance: Optional["ConfigLoader"] = None
    _config: dict[str, Any] | None = None

    def __new__(cls) -> "ConfigLoader":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize configuration loader."""
        if self._config is None:
            self._load_config()

    def _load_config(self) -> None:
        """Load configuration from files and environment."""
        # Load environment variables
        load_dotenv()

        # Determine config directory
        config_dir = Path(__file__).parent.parent.parent / "config"

        # Load main config
        config_path = config_dir / "config.json"
        with open(config_path) as f:
            self._config = json.load(f)

        # Override with environment variables
        self._apply_env_overrides()

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        if self._config is None:
            return

        # Gemini API key
        if api_key := os.getenv("GOOGLE_API_KEY"):
            self._config.setdefault("gemini", {})["api_key"] = api_key

        # Cache settings
        if cache_enabled := os.getenv("CACHE_ENABLED"):
            self._config.setdefault("cache", {})["enabled"] = cache_enabled.lower() == "true"

        if cache_dir := os.getenv("CACHE_DIR"):
            self._config.setdefault("cache", {})["cache_dir"] = cache_dir

        # Logging settings
        if log_level := os.getenv("LOG_LEVEL"):
            self._config.setdefault("logging", {})["level"] = log_level

        if log_dir := os.getenv("LOG_DIR"):
            self._config.setdefault("logging", {})["log_dir"] = log_dir

        # Output directory
        if output_dir := os.getenv("OUTPUT_DIR"):
            self._config["output_dir"] = output_dir

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration key (supports dot notation, e.g., "gemini.model_text")
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config = ConfigLoader()
            >>> model = config.get("gemini.model_text")
        """
        if self._config is None:
            return default

        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_all(self) -> dict[str, Any]:
        """
        Get entire configuration dictionary.

        Returns:
            Complete configuration dictionary
        """
        return self._config.copy() if self._config else {}

    def reload(self) -> None:
        """Reload configuration from files."""
        self._config = None
        self._load_config()


# Global configuration loader instance
_config_loader = ConfigLoader()


def load_config() -> dict[str, Any]:
    """
    Load and return the complete configuration.

    Returns:
        Configuration dictionary

    Example:
        >>> config = load_config()
        >>> print(config["gemini"]["model_text"])
    """
    return _config_loader.get_all()


def get_config(key: str, default: Any = None) -> Any:
    """
    Get a specific configuration value.

    Args:
        key: Configuration key (supports dot notation)
        default: Default value if key not found

    Returns:
        Configuration value or default

    Example:
        >>> api_key = get_config("gemini.api_key")
    """
    return _config_loader.get(key, default)


def reload_config() -> None:
    """
    Reload configuration from files.

    Useful for testing or when configuration files change.
    """
    _config_loader.reload()
