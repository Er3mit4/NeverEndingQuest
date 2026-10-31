"""Durable OpenCode Go settings (key, model choice and the catalogue cache).

The game's settings and secret storage stay in :mod:`model_config`; this module
only names the OpenCode Go fields, so upstream keeps one storage contract.
"""

from __future__ import annotations

import json
import os

DEFAULT_MODEL = "deepseek-v4.1-flash"
KEY_PLACEHOLDER = "your_opencodego_api_key_here"
AUTH_FILE = os.path.join(
    os.environ.get("USERPROFILE")
    or os.environ.get("HOME")
    or os.path.expanduser("~"),
    ".local", "share", "opencode", "auth.json",
)


def _model_config():
    import model_config

    return model_config


def _read_opencode_auth_key():
    """Best-effort read of the opencode-go key from the OpenCode CLI auth file.

    Returns "" when absent/unreadable -- never raises. The file is JSON whose
    top-level keys are provider ids; the "opencode-go" entry carries {"key": ...}.
    """
    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        entry = data.get("opencode-go") or {}
        key = entry.get("key") if isinstance(entry, dict) else None
        return key.strip() if isinstance(key, str) else ""
    except Exception:
        return ""


def persist_key(api_key):
    """Store the OpenCode Go key durably: OS credential store when one exists."""
    config = _model_config()
    config._migrate_plaintext_secrets(config._load_user_settings())
    if api_key:
        config._store_credential("opencodego_api_key", api_key)
    else:
        config._forget_credential("opencodego_api_key")


def has_key():
    """True if a real OpenCode Go key is available (UI-stored or CLI auth file)."""
    config = _model_config()
    if config._read_credential("opencodego_api_key"):
        return True
    return bool(_read_opencode_auth_key())


def get_key():
    """Return the OpenCode Go key to authenticate with, or "" when none.

    Priority: OS-credential-store/UI key -> OpenCode CLI auth.json entry ->
    a live config.OPENCODEGO_API_KEY override (skipping the placeholder).
    """
    config = _model_config()
    key = config._read_credential("opencodego_api_key")
    if key:
        return key
    key = _read_opencode_auth_key()
    if key:
        return key
    import sys

    config_mod = sys.modules.get("config")
    if config_mod is not None:
        value = getattr(config_mod, "OPENCODEGO_API_KEY", "")
        if isinstance(value, str) and value.strip() and \
                value.strip() != KEY_PLACEHOLDER:
            return value.strip()
    return ""


def apply_persisted_key():
    """Push a stored OpenCode Go key into the live config module so every
    reader of config.OPENCODEGO_API_KEY uses it with ZERO reader edits.
    No-op when no key is available (config.py value wins)."""
    key = get_key()
    if not key:
        return
    import sys

    if "config" in sys.modules:
        setattr(sys.modules["config"], "OPENCODEGO_API_KEY", key)


def get_model():
    """The OpenCode Go model every call uses (player choice, else the default).

    One model serves every callsite: the relay's plan is a subscription, so the
    player picks the model once in Settings -> AI Provider instead of per task.
    """
    value = _model_config()._load_user_settings().get("opencodego_model")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return DEFAULT_MODEL


def persist_model(model_id):
    """Save the OpenCode Go model choice; returns the value now in effect."""
    value = model_id.strip() if isinstance(model_id, str) else ""
    if not value:
        raise ValueError("Choose an OpenCode Go model.")
    if len(value) > 80 or not all(ch.isalnum() or ch in "._:-/" for ch in value):
        raise ValueError("That is not a valid OpenCode Go model id.")
    config = _model_config()
    settings = config._load_user_settings()
    if value == DEFAULT_MODEL:
        settings.pop("opencodego_model", None)
    else:
        settings["opencodego_model"] = value
    config._save_user_settings(settings)
    return value


def get_models_cache():
    """The last catalogue fetched from the relay ({"models", "fetched_at"})."""
    cache = _model_config()._load_user_settings().get("opencodego_models_cache")
    return cache if isinstance(cache, dict) else {}


def persist_models_cache(cache):
    """Store the catalogue so the picker is filled before the first fetch."""
    if not isinstance(cache, dict):
        raise TypeError("OpenCode Go model cache must be a dict")
    config = _model_config()
    settings = config._load_user_settings()
    settings["opencodego_models_cache"] = {
        "models": cache.get("models") if isinstance(cache.get("models"), list) else [],
        "fetched_at": cache.get("fetched_at"),
    }
    config._save_user_settings(settings)
