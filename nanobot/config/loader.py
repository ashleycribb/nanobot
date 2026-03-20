"""Configuration loading utilities."""

import json
import os
from pathlib import Path

from nanobot.config.schema import Config


def get_config_path() -> Path:
    """Get the default configuration file path."""
    return Path.home() / ".nanobot" / "config.json"


def get_data_dir() -> Path:
    """Get the nanobot data directory."""
    from nanobot.utils.helpers import get_data_path
    return get_data_path()


def load_config(config_path: Path | None = None) -> Config:
    """
    Load configuration from file or create default.

    Args:
        config_path: Optional path to config file. Uses default if not provided.

    Returns:
        Loaded configuration object.
    """
    path = config_path or get_config_path()

    data = {}

    # 1. Load from file if exists
    if path.exists():
        try:
            with open(path) as f:
                file_data = json.load(f)
            data = _migrate_config(file_data)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Failed to load config from {path}: {e}")
            print("Using default configuration or environment variables.")

    # 2. Load from environment variable (JSON blob)
    env_config_json = os.environ.get("NANOBOT_CONFIG_JSON")
    if env_config_json:
        try:
            env_data = json.loads(env_config_json)
            env_data = _migrate_config(env_data)
            _deep_merge(data, env_data)
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse NANOBOT_CONFIG_JSON: {e}")

    # 3. Create Config object (Pydantic will also read individual env vars for missing fields)
    return Config(**data)


def save_config(config: Config, config_path: Path | None = None) -> None:
    """
    Save configuration to file.

    Args:
        config: Configuration to save.
        config_path: Optional path to save to. Uses default if not provided.
    """
    path = config_path or get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = config.model_dump(by_alias=True)

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _migrate_config(data: dict) -> dict:
    """Migrate old config formats to current."""
    # Move tools.exec.restrictToWorkspace → tools.restrictToWorkspace
    tools = data.get("tools", {})
    if isinstance(tools, dict):
        exec_cfg = tools.get("exec", {})
        if isinstance(exec_cfg, dict) and "restrictToWorkspace" in exec_cfg and "restrictToWorkspace" not in tools:
            tools["restrictToWorkspace"] = exec_cfg.pop("restrictToWorkspace")
    return data


def _deep_merge(target: dict, source: dict) -> dict:
    """
    Recursively merge source dictionary into target dictionary.

    Args:
        target: The dictionary to merge into.
        source: The dictionary with updates.

    Returns:
        The updated target dictionary.
    """
    for k, v in source.items():
        if (
            k in target
            and isinstance(target[k], dict)
            and isinstance(v, dict)
        ):
            _deep_merge(target[k], v)
        else:
            target[k] = v
    return target
