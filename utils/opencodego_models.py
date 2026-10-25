"""OpenCode Go: the plan's model catalogue, wire routing and the cached list.

The Go plan serves several wire protocols behind one base URL, so the model id
alone decides how a request must be sent (OpenCode's published Go endpoint
table, docs/go, and the routing table Hermes Agent uses for the same relay):

* ``gpt-*``, ``grok-*``, ``muse-spark*``      -> OpenAI Responses
* ``claude-*``, ``minimax-*``, ``qwen*``      -> Anthropic Messages
* ``gemini-*``                                -> Google generateContent
* everything else                             -> Chat Completions

The list itself is discovered from the relay's ``/v1/models`` on service start,
cached in ``user_settings.json`` and refreshed on demand. When discovery cannot
run (no key, expired key, offline) the plan's published list below is used, so
the picker never goes empty.

Nothing here stores or prints the key.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone

# The relay's model list endpoint (bare ids; same host the calls use).
MODELS_URL = "https://opencode.ai/zen/go/v1/models"
CACHE_TTL_SECONDS = 6 * 3600
# A failed fetch is not retried on every panel open: one attempt per window.
RETRY_SECONDS = 60
REQUEST_TIMEOUT_SECONDS = 20.0
USER_AGENT = "NeverEndingQuest/1.0"

# model-id prefix -> wire transport, checked in order.
_TRANSPORT_PREFIXES = (
    (("gpt-", "grok-", "muse-spark"), "responses"),
    (("claude-", "qwen", "union-alpha"), "anthropic"),
    (("gemini-",), "google"),
)

# Ids whose published endpoint differs from their family's usual wire (the
# plan's table): MiniMax M3 is Anthropic-wire, its 3.1 sibling is not.
_TRANSPORT_EXACT = {
    "minimax-m3": "anthropic",
    "minimax-m3.1-flash": "chat",
    "minimax-m2.7": "anthropic",
    "minimax-m2.5": "anthropic",
}

TRANSPORT_LABELS = {
    "chat": "Chat Completions",
    "responses": "Responses API",
    "anthropic": "Anthropic Messages",
    "google": "Google generateContent",
}

# Transports this client can serve today.
SUPPORTED_TRANSPORTS = frozenset({"chat", "responses", "anthropic"})

# Offline floor: the Go plan's published list (opencode.ai/en/docs/go,
# 2026-10-25) with the names the plan gives them. Live discovery wins.
FALLBACK_MODELS = (
    ("deepseek-v4.1-flash", "DeepSeek V4.1 Flash"),
    ("deepseek-v4-pro", "DeepSeek V4 Pro"),
    ("glm-5.3-flash", "GLM-5.3-Flash"),
    ("glm-5.3", "GLM-5.3"),
    ("glm-5.2", "GLM-5.2"),
    ("kimi-k3.1-pro", "Kimi K3.1 Pro"),
    ("kimi-k3", "Kimi K3"),
    ("kimi-k2.7-code", "Kimi K2.7 Code"),
    ("minimax-m3.1-flash", "MiniMax M3.1 Flash"),
    ("minimax-m3", "MiniMax M3"),
    ("qwen3.8-max", "Qwen3.8 Max"),
    ("qwen3.8-flash", "Qwen3.8 Flash"),
    ("qwen3.7-plus", "Qwen3.7 Plus"),
    ("mimo-v2.6-flash", "MiMo-V2.6-Flash"),
    ("mimo-v2.6-pro", "MiMo-V2.6-Pro"),
    ("mimo-v2.5", "MiMo-V2.5"),
    ("mimo-v2.5-pro", "MiMo-V2.5-Pro"),
    ("longcat-2.0", "LongCat-2.0"),
    ("step-5-preview", "Step 5 Preview"),
    ("hy4-preview", "Hy4 preview"),
    ("hy3", "Hy3"),
    ("beam-free", "Beam Free"),
    ("gpt-6-luna", "GPT 6 Luna"),
    ("gpt-5.6-luna", "GPT 5.6 Luna"),
    ("grok-4.7", "Grok 4.7"),
    ("claude-haiku-5-5", "Claude Haiku 5.5"),
    ("muse-spark-1.3-contributor", "Muse Spark 1.3 Contributor"),
    ("muse-spark-1.2-contributor", "Muse Spark 1.2 Contributor"),
    ("gemini-4-argon", "Gemini 4 Argon"),
)

_LOCK = threading.Lock()
_STATE = {"models": [], "source": "none", "fetched_at": None, "error": None,
          "attempted_at": None}
_REFRESHING = threading.Event()


def transport_for(model_id):
    """Return the wire transport the Go relay publishes for this model id."""
    normalized = str(model_id or "").strip().lower()
    if normalized in _TRANSPORT_EXACT:
        return _TRANSPORT_EXACT[normalized]
    for prefixes, transport in _TRANSPORT_PREFIXES:
        if normalized.startswith(prefixes):
            return transport
    return "chat"


def is_supported(model_id):
    return transport_for(model_id) in SUPPORTED_TRANSPORTS


def adjust_reasoning_effort(model_id, effort):
    """Return the effort to send for this Go model, or None to omit it.

    Only the contracts the relay documents are used: DeepSeek V4 thinking models
    take low|high|max, GLM-5.2 takes high|max, and every other Go model is left
    on its server default (sending a level a model does not implement is a 400,
    and one bad level would break every callsite for that provider).
    """
    if effort is None:
        return None
    value = str(effort).strip().lower()
    if not value or value == "none":
        value = "low"
    model = str(model_id or "").strip().lower()
    if model.startswith("deepseek-v") or model in ("deepseek-reasoner", "deepseek-flash"):
        return value if value in ("low", "high", "max") else "low"
    if model.startswith("glm-5.2"):
        return "max" if value == "max" else "high"
    return None


def _label_for(model_id, raw):
    """Player-facing name: the relay's own name when it sends one."""
    if isinstance(raw, dict):
        for field in ("name", "display_name", "displayName"):
            value = raw.get(field)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return model_id


def normalize_rows(rows):
    """Turn a raw ``/models`` payload into the picker's rows (deduped)."""
    if isinstance(rows, dict):
        rows = rows.get("data") or rows.get("models") or []
    if not isinstance(rows, (list, tuple)):
        return []
    result = []
    seen = set()
    for item in rows:
        raw = item
        if isinstance(item, str):
            model_id = item.strip()
        elif isinstance(item, dict):
            model_id = str(item.get("id") or item.get("model") or "").strip()
        else:
            model_id = ""
        if not model_id or model_id in seen:
            continue
        seen.add(model_id)
        transport = transport_for(model_id)
        result.append({
            "id": model_id,
            "label": _label_for(model_id, raw),
            "transport": transport,
            "transport_label": TRANSPORT_LABELS.get(transport, transport),
            "supported": transport in SUPPORTED_TRANSPORTS,
        })
    return result


def fallback_rows():
    return normalize_rows([{"id": model_id, "name": label}
                           for model_id, label in FALLBACK_MODELS])


def _request_headers(key):
    headers = {
        "Authorization": "Bearer %s" % key,
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    try:
        from utils.conversation_identity import current_conversation_id
        headers["x-opencode-session"] = current_conversation_id()
    except Exception:
        pass
    return headers


def fetch_rows(key, timeout=REQUEST_TIMEOUT_SECONDS):
    """GET the relay's model list. Raises on transport/auth/shape failure."""
    if not key:
        raise ValueError("no OpenCode Go key")
    import httpx

    response = httpx.get(MODELS_URL, headers=_request_headers(key), timeout=timeout)
    response.raise_for_status()
    rows = normalize_rows(response.json())
    if not rows:
        raise ValueError("the relay listed no models")
    return rows


def _now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _reason(exc, key):
    """A short, secret-free reason the Settings panel can show."""
    if not key:
        return "No OpenCode Go key is set."
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if status in (401, 403):
        return "The OpenCode Go key was refused (HTTP %s). Paste a current key." % status
    if status == 404:
        return "The relay did not offer its model list (HTTP 404)."
    if status:
        return "The relay answered HTTP %s while listing models." % status
    text = str(exc).strip() or exc.__class__.__name__
    return text[:200]


def _fresh(fetched_at):
    if not fetched_at:
        return False
    try:
        stamp = datetime.fromisoformat(str(fetched_at).replace("Z", "+00:00"))
    except ValueError:
        return False
    return (datetime.now(timezone.utc) - stamp).total_seconds() < CACHE_TTL_SECONDS


def _load_cached():
    import model_config
    cached = model_config.get_opencodego_models_cache()
    rows = normalize_rows(cached.get("models"))
    return rows, cached.get("fetched_at")


def _store(models, source, fetched_at, error):
    _STATE.update(models=models, source=source, fetched_at=fetched_at, error=error)


def _persist(models, fetched_at):
    import model_config
    try:
        model_config.persist_opencodego_models_cache({"models": models, "fetched_at": fetched_at})
    except Exception:
        # A read-only settings file must not break the picker; the in-memory
        # list still serves this session.
        pass


def refresh(force=False, key=None):
    """Refresh the catalogue; returns the state dict.

    Order: a live fetch (when a key exists) -> the last cached list -> the
    published floor. Never raises: a failure is reported in ``error``.
    """
    with _LOCK:
        rows, cached_at = _load_cached()
        if not force and _STATE["models"] and _fresh(_STATE["fetched_at"]):
            return dict(_STATE)
        if not force and not _STATE["models"] and rows and _fresh(cached_at):
            _store(rows, "cache", cached_at, None)
            return dict(_STATE)
        import model_config
        key = model_config.get_opencodego_key() if key is None else key
        if not key:
            rows = rows or fallback_rows()
            _store(rows, "cache" if cached_at else "fallback", cached_at,
                   "No OpenCode Go key is set.")
            return dict(_STATE)
        # One network attempt per retry window; payload() reads this so a bad
        # key cannot make every Settings open wait on the relay.
        _STATE["attempted_at"] = datetime.now(timezone.utc)
        try:
            live = fetch_rows(key)
        except Exception as exc:
            reason = _reason(exc, key)
            rows = rows or fallback_rows()
            source = "cache" if cached_at else "fallback"
            stamp = cached_at if cached_at else None
            _store(rows, source, stamp, reason)
            return dict(_STATE)
        stamp = _now()
        _store(live, "live", stamp, None)
        _persist(live, stamp)
        return dict(_STATE)


def start_background_refresh():
    """Warm the catalogue once, off the caller's thread (service start)."""
    if _REFRESHING.is_set():
        return

    def worker():
        try:
            refresh(force=True)
        finally:
            _REFRESHING.clear()

    _REFRESHING.set()
    thread = threading.Thread(target=worker, name="opencodego-models", daemon=True)
    thread.start()


def state():
    """The current catalogue without touching the network."""
    with _LOCK:
        if _STATE["models"]:
            return dict(_STATE)
        rows, cached_at = _load_cached()
        if rows:
            _store(rows, "cache", cached_at, None)
        else:
            _store(fallback_rows(), "fallback", None, None)
        return dict(_STATE)


def selected_model():
    import model_config
    return model_config.get_opencodego_model()


def _due(attempted_at):
    if not isinstance(attempted_at, datetime):
        return True
    return (datetime.now(timezone.utc) - attempted_at).total_seconds() >= RETRY_SECONDS


def payload(refresh_if_stale=False):
    """The Socket.IO payload the Settings panel renders."""
    if refresh_if_stale:
        current = state()
        if not _fresh(current["fetched_at"]) and _due(current.get("attempted_at")):
            refresh(force=False)
    current = state()
    selected = selected_model()
    return {
        "models": current["models"],
        "selected": selected,
        "source": current["source"],
        "fetched_at": current["fetched_at"],
        "error": current["error"],
    }
