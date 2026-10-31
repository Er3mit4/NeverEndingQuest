"""OpenCode Go OpenAI-compatible connection (endpoint, key, headers, wire)."""

from __future__ import annotations

from . import catalog, settings

BASE_URL = "https://opencode.ai/zen/go/v1"
# The same relay serves the Anthropic wire one level up: the SDK appends
# /v1/messages itself.
ANTHROPIC_BASE_URL = "https://opencode.ai/zen/go"
USER_AGENT = "NeverEndingQuest/1.0"


def session_id():
    """The conversation identity every provider child inherits."""
    from utils.conversation_identity import current_conversation_id

    return current_conversation_id()


def connection(endpoint_override=None, model=None):
    """Resolve one OpenAI-compatible endpoint without mixing credentials.

    The player's chosen model decides both the model id and the wire transport
    (Chat Completions, Responses or Anthropic Messages), because the plan serves
    different protocols per model behind one relay.
    """
    selected = (model or "").strip() or settings.get_model() or settings.DEFAULT_MODEL
    transport = catalog.transport_for(selected)
    return {
        "base_url": (ANTHROPIC_BASE_URL if transport == "anthropic" else BASE_URL),
        "api_key": settings.get_key() or "not-needed",
        "model": selected,
        "json_object": transport != "anthropic",
        "headers": {
            "x-opencode-session": session_id(),
            "User-Agent": USER_AGENT,
        },
        "transport": transport,
        # api_client asks the connection how to normalize reasoning effort, so
        # the provider's ladder rules live here, not in the router.
        "effort_normalizer": catalog.adjust_reasoning_effort,
    }
