"""
OpenAI Client Factory
Provides centralized client creation with LM Studio support
"""

import socket

import httpx
from openai import OpenAI
import config


# TCP keepalive on every provider socket (#409, D-409-3, owner-ruled
# 2026-09-19): a path that silently stops acknowledging (NAT/vSwitch drop,
# dead peer) surfaces as a socket error within idle + interval * count
# seconds and feeds the existing reissue loop, instead of a read that waits
# until the generation backstop. A live peer that is merely slow keeps
# answering the probes and is never touched, so this is not a deadline on
# the model's work. Kernel defaults (7200 s idle on Linux) never notice a
# dead path inside a ten-minute wait. The option list is assembled once from
# the constants this platform's socket module exposes (Linux, macOS and
# Windows 10+ expose all four on Python 3.10).
_KEEPALIVE_IDLE_SECONDS = 10
_KEEPALIVE_INTERVAL_SECONDS = 5
_KEEPALIVE_PROBE_COUNT = 3


def _provider_socket_options():
    options = [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)]
    for name, value in (
        ("TCP_KEEPIDLE", _KEEPALIVE_IDLE_SECONDS),
        ("TCP_KEEPINTVL", _KEEPALIVE_INTERVAL_SECONDS),
        ("TCP_KEEPCNT", _KEEPALIVE_PROBE_COUNT),
    ):
        constant = getattr(socket, name, None)
        if constant is not None:
            options.append((socket.IPPROTO_TCP, constant, value))
    return options


PROVIDER_SOCKET_OPTIONS = tuple(_provider_socket_options())


# OpenCode Go subscription endpoint (OpenAI-compatible Chat Completions).
# deepseek-v4.1-flash and the other Go models live at
# https://opencode.ai/zen/go/v1/chat/completions (Bearer auth).
DEFAULT_OPENCODEGO_BASE_URL = "https://opencode.ai/zen/go/v1"

def _opencodego_session_id():
    """Return the game-owned identity inherited by subprocess generations."""
    from utils.conversation_identity import current_conversation_id
    return current_conversation_id()


def _provider_http_client():
    """One httpx client shape for every OpenAI-compatible provider."""
    return httpx.Client(
        transport=httpx.HTTPTransport(socket_options=list(PROVIDER_SOCKET_OPTIONS)),
    )


def compatible_connection(provider, endpoint_override=None):
    """Resolve one OpenAI-compatible endpoint without mixing credentials."""
    import model_config
    if provider == "lmstudio":
        ep = endpoint_override if endpoint_override is not None else model_config.get_local_endpoint()
        return {
            "base_url": ep["base_url"],
            "api_key": ep.get("api_key") or "not-needed",
            "model": ep.get("model") or "",
            "json_object": False,
            "headers": {},
        }
    if provider == "opencodego":
        return {
            "base_url": DEFAULT_OPENCODEGO_BASE_URL,
            "api_key": model_config.get_opencodego_key() or "not-needed",
            "model": "deepseek-v4.1-flash",
            "json_object": True,
            "headers": {
                "x-opencode-session": _opencodego_session_id(),
                "User-Agent": "NeverEndingQuest/1.0",
            },
        }
    raise ValueError("Unsupported compatible endpoint: %s" % provider)


def get_openai_client(provider=None, endpoint_override=None):
    """
    Create and return an OpenAI client configured for the active provider.

    Returns:
        OpenAI: Configured OpenAI client

    Behavior:
        - If MODEL_PROVIDER == "lmstudio": Connects to localhost:1234 (local LM Studio)
        - If MODEL_PROVIDER == "opencodego": Connects to opencode.ai/zen/go (DeepSeek)
        - Otherwise: Connects to OpenAI API (requires config.OPENAI_API_KEY)

    Usage:
        from utils.openai_client import get_openai_client
        client = get_openai_client()
        response = client.chat.completions.create(...)
    """
    if provider is None:
        import model_config
        provider = model_config.get_provider()

    if provider in ("lmstudio", "opencodego"):
        ep = compatible_connection(provider, endpoint_override)
        return OpenAI(
            base_url=ep["base_url"],
            api_key=ep["api_key"],
            default_headers=ep["headers"],
            http_client=_provider_http_client(),
        )
    else:
        # Connect to OpenAI API (default)
        # Requires valid API key in config.py
        return OpenAI(
            api_key=config.OPENAI_API_KEY,
            http_client=_provider_http_client(),
        )


def is_using_lm_studio():
    """
    Check if the game is configured to use LM Studio.

    Returns:
        bool: True if MODEL_PROVIDER is "lmstudio", False otherwise

    Usage:
        from utils.openai_client import is_using_lm_studio
        if is_using_lm_studio():
            print("Running with local LM Studio")
    """
    from model_config import MODEL_PROVIDER
    return MODEL_PROVIDER == "lmstudio"
