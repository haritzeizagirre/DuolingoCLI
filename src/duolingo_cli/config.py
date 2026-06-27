"""
Configuration management for DuolingoCLI.

Handles JWT token storage, user preferences, and API settings.
Token is stored securely via keyring (OS credential store) or 
falls back to a local config file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import click

CONFIG_DIR = Path(click.get_app_dir("duolingo-cli"))
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKEN_SERVICE = "duolingo-cli"
TOKEN_USERNAME = "jwt_token"


def _ensure_config_dir() -> None:
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _load_config() -> dict:
    """Load config from JSON file."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {}


def _save_config(data: dict) -> None:
    """Save config to JSON file."""
    _ensure_config_dir()
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_token(token: str) -> None:
    """
    Save JWT token. Tries keyring first, falls back to config file.
    """
    try:
        import keyring
        keyring.set_password(TOKEN_SERVICE, TOKEN_USERNAME, token)
    except Exception:
        # Fallback to file-based storage
        config = _load_config()
        config["jwt_token"] = token
        _save_config(config)


def get_token() -> Optional[str]:
    """
    Retrieve JWT token. Tries keyring first, falls back to config file.
    """
    try:
        import keyring
        token = keyring.get_password(TOKEN_SERVICE, TOKEN_USERNAME)
        if token:
            return token
    except Exception:
        pass

    config = _load_config()
    return config.get("jwt_token")


def delete_token() -> None:
    """Delete stored JWT token."""
    try:
        import keyring
        keyring.delete_password(TOKEN_SERVICE, TOKEN_USERNAME)
    except Exception:
        pass

    config = _load_config()
    config.pop("jwt_token", None)
    _save_config(config)


def get_user_id() -> Optional[str]:
    """Get cached user ID."""
    return _load_config().get("user_id")


def save_user_id(user_id: str) -> None:
    """Cache user ID."""
    config = _load_config()
    config["user_id"] = user_id
    _save_config(config)


def get_username() -> Optional[str]:
    """Get cached username."""
    return _load_config().get("username")


def save_username(username: str) -> None:
    """Cache username."""
    config = _load_config()
    config["username"] = username
    _save_config(config)


def get_display_language() -> str:
    """Get UI language preference (default: en)."""
    return _load_config().get("from_language", "en")


def save_display_language(lang: str) -> None:
    """Save UI language preference."""
    config = _load_config()
    config["from_language"] = lang
    _save_config(config)
