"""OpenCode Go provider declaration.

The model stays ``deepseek-v4.1-flash`` by default, with the per-callsite
effort ladder the fork has always used (low everywhere, high for T017 and the
third T097 attempt, max for T026).
"""

from __future__ import annotations

from ..opencodego import catalog, connection, settings, web
from ..spec import ProviderSpec

_MODEL = settings.DEFAULT_MODEL

# Named profile dicts. They are injected into ``model_config`` so every existing
# callsite map (``config.MINI_UTIL_OPENCODEGO`` etc.) keeps working unchanged.
PROFILES = {
    "DM_FULL_MODEL_OPENCODEGO": {"model": _MODEL, "reasoning_effort": "low"},
    "DM_MINI_MODEL_OPENCODEGO": {"model": _MODEL, "reasoning_effort": "low"},
    "OPENCODEGO_LOW": {"model": _MODEL, "reasoning_effort": "low"},
    "OPENCODEGO_HIGH": {"model": _MODEL, "reasoning_effort": "high"},
    "OPENCODEGO_MAX": {"model": _MODEL, "reasoning_effort": "max"},
    "CHAR_EFFECTS_OPENCODEGO": {"model": _MODEL, "reasoning_effort": "low"},
    "MINI_UTIL_OPENCODEGO": {"model": _MODEL, "reasoning_effort": "low"},
    "DM_MAIN_OPENCODEGO": {"model": _MODEL, "reasoning_effort": "low"},
    "NPC_VOICE_T105_OPENCODEGO": {"model": _MODEL, "reasoning_effort": "low"},
    "NPC_PROFILE_T107_OPENCODEGO": {"model": _MODEL, "reasoning_effort": "low"},
}

LADDERS = {
    "T017": ("OPENCODEGO_HIGH",),
    "T026": ("OPENCODEGO_MAX",),
    "T097": ("OPENCODEGO_LOW", "OPENCODEGO_LOW", "OPENCODEGO_HIGH"),
}


def constraints(model, kwargs):
    """DeepSeek V4 accepts low|high|max only; a stray "none" becomes "low"."""
    if "deepseek" in str(model or "").lower():
        reasoning = kwargs.get("reasoning_effort")
        if reasoning and str(reasoning).lower() == "none":
            kwargs["reasoning_effort"] = "low"


SPEC = ProviderSpec(
    name="opencodego",
    display_name="OpenCode Go",
    provider_models={"full": _MODEL, "mini": _MODEL},
    profiles=PROFILES,
    ladders=LADDERS,
    default_ladder=("OPENCODEGO_LOW",),
    connection=connection.connection,
    constraints=constraints,
    credentials_available=web.credentials_available,
    apply_persisted_key=settings.apply_persisted_key,
    register_socket_handlers=web.register_socket_handlers,
    start_background_jobs=web.start_background_jobs,
)
