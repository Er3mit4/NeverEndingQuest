"""Installs the local provider bridges into the game's small hook points.

Nothing here imports a game module at import time. The hooks pass their own
module namespace in, so registration follows whatever the current upstream
version defines (no private import of ``model_registry``/``model_config``).
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Optional


def _specs():
    from .providers import SPECS

    return SPECS


def provider_names():
    return tuple(spec.name for spec in _specs())


def _spec(provider: str):
    for spec in _specs():
        if spec.name == provider:
            return spec
    return None


def extend_model_registry(namespace: Mapping[str, Any]) -> None:
    """Add local providers to ``model_registry`` before bindings are frozen.

    Called from ``model_registry`` with its module globals: the provider names
    join ``SUPPORTED_PROVIDERS`` and every callsite declaration gains its
    ladder under ``CallsiteBinding.extra``.
    """
    specs = _specs()
    if not specs:
        return
    known = tuple(namespace.get("SUPPORTED_PROVIDERS", ()))
    namespace["SUPPORTED_PROVIDERS"] = known + tuple(
        spec.name for spec in specs if spec.name not in known
    )
    replace = namespace["replace"]
    declarations = []
    for declaration in namespace["_DECLARATIONS"]:
        extra = dict(getattr(declaration, "extra", {}) or {})
        for spec in specs:
            ladder = spec.ladder_for(declaration.task_id)
            if ladder:
                extra[spec.name] = ladder
        declarations.append(replace(declaration, extra=extra))
    namespace["_DECLARATIONS"][:] = declarations


def install_model_extensions(namespace: Mapping[str, Any]) -> None:
    """Add local providers to ``model_config`` after its own definitions.

    Injects the named profile dicts the registry bindings reference, adds the
    provider entry, and re-applies the persisted credential.
    """
    provider_models = namespace.get("PROVIDER_MODELS")
    for spec in _specs():
        if isinstance(provider_models, dict):
            provider_models[spec.name] = dict(spec.provider_models)
        for name, profile in spec.profiles.items():
            namespace[name] = dict(profile)
        if spec.apply_persisted_key is not None:
            spec.apply_persisted_key()


def connection_for(provider: str) -> Optional[Callable[..., Mapping[str, Any]]]:
    spec = _spec(provider)
    return spec.connection if spec is not None else None


def constraints_for(provider: str) -> Optional[Callable[[str, dict], None]]:
    spec = _spec(provider)
    return spec.constraints if spec is not None else None


def credentials_available(provider: str) -> Optional[bool]:
    spec = _spec(provider)
    if spec is None or spec.credentials_available is None:
        return None
    return bool(spec.credentials_available())


def display_name(provider: str) -> Optional[str]:
    spec = _spec(provider)
    return spec.display_name if spec is not None else None


def register_web_handlers(socketio, emit) -> None:
    """Register each local provider's Settings events."""
    for spec in _specs():
        if spec.register_socket_handlers is not None:
            spec.register_socket_handlers(socketio, emit)


def start_background_jobs() -> None:
    """Start on-demand warmups (never on import)."""
    for spec in _specs():
        if spec.start_background_jobs is not None:
            spec.start_background_jobs()
