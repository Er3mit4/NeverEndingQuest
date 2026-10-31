"""Local provider bridge for this fork (see ``fork_ext/opencodego``)."""

from .registry import (  # noqa: F401
    connection_for,
    constraints_for,
    credentials_available,
    display_name,
    extend_model_registry,
    install_model_extensions,
    provider_names,
    register_web_handlers,
    start_background_jobs,
)

__all__ = [
    "connection_for",
    "constraints_for",
    "credentials_available",
    "display_name",
    "extend_model_registry",
    "install_model_extensions",
    "provider_names",
    "register_web_handlers",
    "start_background_jobs",
]
