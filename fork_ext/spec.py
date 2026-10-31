"""The contract a local provider bridge implements."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Sequence


@dataclass(frozen=True)
class ProviderSpec:
    """Everything the game needs to know about one local provider.

    Callables are resolved lazily at call time, so installing the spec during
    ``model_config`` import never imports a transport or the web layer.
    """

    name: str
    display_name: str
    provider_models: Mapping[str, str]
    profiles: Mapping[str, Mapping[str, Any]]
    ladders: Mapping[str, Sequence[str]] = field(default_factory=dict)
    default_ladder: Sequence[str] = ()
    connection: Optional[Callable[..., Mapping[str, Any]]] = None
    constraints: Optional[Callable[[str, dict], None]] = None
    credentials_available: Optional[Callable[[], bool]] = None
    apply_persisted_key: Optional[Callable[[], None]] = None
    register_socket_handlers: Optional[Callable[[Any, Callable], None]] = None
    start_background_jobs: Optional[Callable[[], None]] = None

    def ladder_for(self, task_id: str) -> tuple:
        return tuple(self.ladders.get(task_id, self.default_ladder))
