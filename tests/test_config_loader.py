import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from nanobot.config.loader import (
    _deep_merge,
    _migrate_config,
    get_config_path,
    get_data_dir,
    load_config,
    save_config,
)
from nanobot.config.schema import Config


def test_get_config_path():
    with patch("pathlib.Path.home", return_value=Path("/mock/home")):
        path = get_config_path()
        assert path == Path("/mock/home/.nanobot/config.json")


def test_get_data_dir():
    with patch("nanobot.utils.helpers.get_data_path", return_value=Path("/mock/data")):
        path = get_data_dir()
        assert path == Path("/mock/data")


def test_migrate_config():
    # Test valid migration
    data = {
        "tools": {
            "exec": {
                "restrictToWorkspace": True,
                "timeout": 30
            }
        }
    }
    migrated = _migrate_config(data)
    assert migrated["tools"]["restrictToWorkspace"] is True
    assert "restrictToWorkspace" not in migrated["tools"]["exec"]
    assert migrated["tools"]["exec"]["timeout"] == 30

    # Test no migration needed
    data = {"tools": {"restrictToWorkspace": False}}
    migrated = _migrate_config(data)
    assert migrated["tools"]["restrictToWorkspace"] is False

    # Test empty / basic structure
    data = {}
    migrated = _migrate_config(data)
    assert migrated == {}


def test_deep_merge():
    target = {
        "a": 1,
        "b": {"c": 2, "d": {"e": 3}},
        "x": 10
    }
    source = {
        "b": {"d": {"e": 4, "f": 5}},
        "x": 20,
        "y": 30
    }
    expected = {
        "a": 1,
        "b": {"c": 2, "d": {"e": 4, "f": 5}},
        "x": 20,
        "y": 30
    }
    result = _deep_merge(target, source)
    assert result == expected


def test_load_config_default(tmp_path):
    # Test loading when config path does not exist
    config_path = tmp_path / "nonexistent.json"

    with patch.dict(os.environ, {}, clear=True):
        config = load_config(config_path)

    assert isinstance(config, Config)
    # Check a default value
    assert config.agents.defaults.model == "anthropic/claude-opus-4-5"


def test_load_config_from_file(tmp_path):
    # Test loading from a valid JSON file
    config_path = tmp_path / "config.json"
    config_data = {
        "agents": {
            "defaults": {
                "model": "test-model-123"
            }
        }
    }
    config_path.write_text(json.dumps(config_data))

    with patch.dict(os.environ, {}, clear=True):
        config = load_config(config_path)

    assert config.agents.defaults.model == "test-model-123"


def test_load_config_invalid_json(tmp_path, capsys):
    # Test loading from an invalid JSON file
    config_path = tmp_path / "config.json"
    config_path.write_text("{ invalid json }")

    with patch.dict(os.environ, {}, clear=True):
        config = load_config(config_path)

    # Should fall back to default
    assert config.agents.defaults.model == "anthropic/claude-opus-4-5"

    # Should print a warning
    captured = capsys.readouterr()
    assert "Warning: Failed to load config" in captured.out
    assert "Using default configuration or environment variables." in captured.out


def test_load_config_env_var(tmp_path):
    # Test loading with NANOBOT_CONFIG_JSON
    config_path = tmp_path / "nonexistent.json"
    env_json = json.dumps({
        "gateway": {
            "port": 9999
        }
    })

    with patch.dict(os.environ, {"NANOBOT_CONFIG_JSON": env_json}):
        config = load_config(config_path)

    assert config.gateway.port == 9999


def test_load_config_invalid_env_var(tmp_path, capsys):
    # Test loading with invalid NANOBOT_CONFIG_JSON
    config_path = tmp_path / "nonexistent.json"

    with patch.dict(os.environ, {"NANOBOT_CONFIG_JSON": "{ invalid }"}):
        config = load_config(config_path)

    # Should print a warning
    captured = capsys.readouterr()
    assert "Warning: Failed to parse NANOBOT_CONFIG_JSON" in captured.out


def test_load_config_file_and_env_var_merge(tmp_path):
    # Test that env vars merge over file config
    config_path = tmp_path / "config.json"
    config_data = {
        "gateway": {
            "host": "127.0.0.1",
            "port": 8080
        }
    }
    config_path.write_text(json.dumps(config_data))

    env_json = json.dumps({
        "gateway": {
            "port": 9090  # Should override the 8080 from file
        }
    })

    with patch.dict(os.environ, {"NANOBOT_CONFIG_JSON": env_json}):
        config = load_config(config_path)

    assert config.gateway.host == "127.0.0.1"  # From file
    assert config.gateway.port == 9090  # From env var


def test_save_config(tmp_path):
    config_path = tmp_path / "saved_config.json"

    # Create a config
    config = Config()
    config.gateway.port = 12345

    # Save it
    save_config(config, config_path)

    # Read it back directly
    assert config_path.exists()
    saved_data = json.loads(config_path.read_text())

    assert saved_data["gateway"]["port"] == 12345
