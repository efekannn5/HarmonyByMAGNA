import os
from pathlib import Path
from typing import Any, Dict

import yaml


class ConfigLoader:
    """Loads YAML configuration into a plain dictionary."""

    @staticmethod
    def load(config_path: str | None = None) -> Dict[str, Any]:
        path = ConfigLoader._resolve_path(config_path)
        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return data

    @staticmethod
    def _resolve_path(path: str | None) -> Path:
        if path:
            candidate = Path(path)
            if candidate.is_file():
                return candidate
        env_path = os.getenv("APP_CONFIG_FILE")
        if env_path:
            candidate = Path(env_path)
            if candidate.is_file():
                return candidate
        default_path = Path(__file__).resolve().parents[2] / "config" / "config.yaml"
        if not default_path.is_file():
            raise FileNotFoundError("Config file not found. Set APP_CONFIG_FILE environment variable.")
        return default_path
