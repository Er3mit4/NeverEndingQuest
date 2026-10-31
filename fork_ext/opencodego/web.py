"""OpenCode Go Settings events and credential check."""

from __future__ import annotations

from . import catalog, settings


def credentials_available():
    """True when a key is available (UI-stored or the OpenCode CLI auth file)."""
    return bool(settings.get_key())


def register_socket_handlers(socketio, emit):
    """Register the provider's Settings events on the shared Socket.IO server."""
    from utils.enhanced_logger import debug, error

    @socketio.on("get_opencodego_key")
    def handle_get_opencodego_key():
        """Report ONLY whether an OpenCode Go key is configured. Never sends the secret."""
        try:
            emit("opencodego_key_status", {"has_key": settings.has_key()})
        except Exception as exc:
            error(f"Error getting opencodego key status: {exc}", exception=exc,
                  category="web_interface")
            emit("opencodego_key_status", {"has_key": False})

    @socketio.on("set_opencodego_key")
    def handle_set_opencodego_key(data):
        """Set the OpenCode Go key from the UI: update config live AND persist. No echo."""
        try:
            import config as _cfg

            api_key = ((data or {}).get("api_key") or "").strip()
            if not api_key:
                # Blank submit: do NOT wipe an existing key. Report status only.
                emit("opencodego_key_status", {"has_key": settings.has_key()})
                return
            _cfg.OPENCODEGO_API_KEY = api_key          # live: config readers
            settings.persist_key(api_key)              # survive restart
            from utils.startup_provider_recovery import notify_configuration_saved
            notify_configuration_saved("opencodego")
            debug("OpenCode Go API key updated via web UI", category="web_interface")
            emit("opencodego_key_status", {"has_key": settings.has_key()}, broadcast=True)
        except Exception as exc:
            error(f"Error setting opencodego key: {exc}", exception=exc,
                  category="web_interface")
            emit("error", {"message": "Failed to set OpenCode Go API key"})  # no key leak

    @socketio.on("get_opencodego_models")
    def handle_get_opencodego_models():
        """List the plan models: live when the key works, else the cache or floor."""
        try:
            emit("opencodego_models", catalog.payload(refresh_if_stale=True))
        except Exception as exc:
            error(f"Error listing OpenCode Go models: {exc}", exception=exc,
                  category="web_interface")
            emit("opencodego_models", {
                "models": [], "selected": "", "source": "none", "fetched_at": None,
                "error": "The OpenCode Go model list could not be read.",
            })

    @socketio.on("refresh_opencodego_models")
    def handle_refresh_opencodego_models():
        """Re-fetch the plan's model list now (the Settings Refresh button)."""
        try:
            catalog.refresh(force=True)
            emit("opencodego_models", catalog.payload(), broadcast=True)
        except Exception as exc:
            error(f"Error refreshing OpenCode Go models: {exc}", exception=exc,
                  category="web_interface")
            emit("error", {"message": "Failed to refresh the OpenCode Go model list"})

    @socketio.on("set_opencodego_model")
    def handle_set_opencodego_model(data):
        """Save the model used by every call (plan subscription = one model)."""
        try:
            selected = settings.persist_model((data or {}).get("model"))
            debug(f"OpenCode Go model set to: {selected}", category="web_interface")
            emit("opencodego_model_changed", {"model": selected}, broadcast=True)
        except (ValueError, TypeError) as exc:
            emit("error", {"message": str(exc)})
        except Exception as exc:
            error(f"Error setting OpenCode Go model: {exc}", exception=exc,
                  category="web_interface")
            emit("error", {"message": "Failed to set the OpenCode Go model"})


def start_background_jobs():
    """Warm the plan catalogue off-thread when the service starts."""
    catalog.start_background_refresh()
