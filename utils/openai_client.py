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

# Stable per-process session id for the Go gateway's x-opencode-session
# header (routing + prompt-cache optimization). One id per game-process run
# mirrors how a coding agent scopes one conversation; generated lazily on
# first OpenCode Go client creation.
_OPENCODEGO_SESSION_ID = None


def _opencodego_session_id():
    """Return this process's stable OpenCode Go session id, creating it once."""
    global _OPENCODEGO_SESSION_ID
    if _OPENCODEGO_SESSION_ID is None:
        import uuid
        _OPENCODEGO_SESSION_ID = str(uuid.uuid4())
    return _OPENCODEGO_SESSION_ID


def _provider_http_client():
    """One httpx client shape for every OpenAI-compatible provider."""
    return httpx.Client(
        transport=httpx.HTTPTransport(socket_options=list(PROVIDER_SOCKET_OPTIONS)),
    )


def get_openai_client(provider=None):
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

    if provider == "lmstudio":
        # Local / OpenAI-compatible server (LM Studio, Ollama, vLLM, OpenRouter,
        # remote host). Endpoint is read live from user_settings.json so a web-UI
        # change applies on the next request with no restart. Defaults preserve
        # the original LM Studio localhost:1234 behavior. (Issue #120)
        import model_config
        ep = model_config.get_local_endpoint()
        return OpenAI(
            base_url=ep["base_url"],
            api_key=ep["api_key"] or "not-needed",
            http_client=_provider_http_client(),
        )
    if provider == "opencodego":
        # OpenCode Go (https://opencode.ai/en/docs/go): OpenAI-compatible
        # Chat Completions endpoint serving deepseek-v4.1-flash and other open
        # models behind the Go subscription. Key source priority: a UI-stored
        # key, then the opencode-go entry the OpenCode CLI persists in
        # auth.json. Read live per call so a Settings change needs no restart.
        #
        # Go requires two extra headers (docs/go/#where-can-i-use-it):
        #   x-opencode-session -- a stable conversation-scoped session id for
        #     routing/prompt-cache optimization. One id per game-process run
        #     keeps all calls of a play session on one stable route.
        #   User-Agent -- the client identifies itself by name, never as the
        #     generic SDK user agent.
        import model_config
        return OpenAI(
            base_url=DEFAULT_OPENCODEGO_BASE_URL,
            api_key=model_config.get_opencodego_key() or "not-needed",
            default_headers={
                "x-opencode-session": _opencodego_session_id(),
                "User-Agent": "NeverEndingQuest/1.0",
            },
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
