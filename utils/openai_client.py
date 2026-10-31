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


def _provider_http_client():
    """One httpx client shape for every OpenAI-compatible provider."""
    return httpx.Client(
        transport=httpx.HTTPTransport(socket_options=list(PROVIDER_SOCKET_OPTIONS)),
    )


_COMPATIBLE_CONNECTION_FACTORIES = {}


def register_compatible_connection(provider, factory):
    """Register a local bridge's OpenAI-compatible endpoint factory.

    ``factory(endpoint_override=..., model=...)`` returns the connection dict
    read by ``api_client`` (base_url, api_key, model, headers, transport).
    """
    _COMPATIBLE_CONNECTION_FACTORIES[str(provider)] = factory


def is_compatible_provider(provider):
    """True when this provider uses the OpenAI-compatible transport."""
    if provider == "lmstudio" or provider in _COMPATIBLE_CONNECTION_FACTORIES:
        return True
    return _fork_connection_factory(provider) is not None


def _fork_connection_factory(provider):
    try:
        from fork_ext.registry import connection_for
    except ImportError:
        return None
    factory = connection_for(provider)
    if factory is not None:
        # Register-on-first-use keeps core import order irrelevant.
        register_compatible_connection(provider, factory)
    return factory


def compatible_connection(provider, endpoint_override=None, model=None):
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
            "transport": "chat",
        }
    factory = _COMPATIBLE_CONNECTION_FACTORIES.get(provider)
    if factory is None:
        factory = _fork_connection_factory(provider)
    if factory is not None:
        return factory(endpoint_override=endpoint_override, model=model)
    raise ValueError("Unsupported compatible endpoint: %s" % provider)


def get_openai_client(provider=None, endpoint_override=None):
    """
    Create and return an OpenAI client configured for the active provider.

    Returns:
        OpenAI: Configured OpenAI client

    Behavior:
        - If MODEL_PROVIDER == "lmstudio": Connects to localhost:1234 (local LM Studio)
        - A local bridge provider (fork_ext): Connects to its registered endpoint
        - Otherwise: Connects to OpenAI API (requires config.OPENAI_API_KEY)

    Usage:
        from utils.openai_client import get_openai_client
        client = get_openai_client()
        response = client.chat.completions.create(...)
    """
    if provider is None:
        import model_config
        provider = model_config.get_provider()

    if is_compatible_provider(provider) or _fork_connection_factory(provider) is not None:
        ep = compatible_connection(provider, endpoint_override)
        return OpenAI(
            base_url=ep["base_url"],
            api_key=ep["api_key"],
            default_headers=ep["headers"],
            http_client=_provider_http_client(),
        )
    else:
        # Connect to OpenAI API (default)
        return openai_api_client()


# The OpenAI API host, pinned (#1399). Without an explicit base_url the SDK
# reads OPENAI_BASE_URL from the environment, which would send the player's
# OpenAI key to whatever host that names.
OPENAI_API_BASE_URL = "https://api.openai.com/v1"


def openai_api_client(api_key=None, **kwargs):
    """The one way to build a client that carries the OpenAI key (#1399).

    base_url is always OPENAI_API_BASE_URL; a caller cannot pass another.
    ``api_key`` defaults to config.OPENAI_API_KEY, read at call time. The
    Local/Custom and OpenCode Go branches above are the only clients built
    elsewhere: they use the player's own endpoint and never the OpenAI key.
    """
    if "base_url" in kwargs:
        raise TypeError("openai_api_client pins base_url to the OpenAI API")
    http_client = kwargs.pop("http_client", None) or _provider_http_client()
    return OpenAI(
        api_key=api_key or config.OPENAI_API_KEY,
        base_url=OPENAI_API_BASE_URL,
        http_client=http_client,
        **kwargs,
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
