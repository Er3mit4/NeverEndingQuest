"""Anthropic Messages transport for OpenCode Go's anthropic-wire models.

The Go relay serves ``claude-*``, ``minimax-*`` and ``qwen*`` only on the
Anthropic wire (``POST <base>/v1/messages``), so these models cannot use the
OpenAI-compatible client at all. This module speaks that wire directly with
``httpx`` and returns the same primitives the OpenAI path assembles, leaving
the provider contract in ``core/ai/api_client.py`` untouched.

Deliberately small and strict:

* The base URL carries no ``/v1`` (the endpoint is ``<base>/v1/messages``).
* ``system`` messages become the top-level ``system`` string; the remaining
  turns alternate user/assistant, merged when the history repeats a role,
  because Anthropic rejects two consecutive turns of the same role.
* JSON mode has no request flag on this wire, so the instruction is appended to
  the system prompt (the game's parsers already tolerate prose, but this keeps
  the one-object contract).
* No ``thinking``/``reasoning_effort`` is sent: the relay's per-model support is
  not published, and an unsupported field is a 400 for every call.
"""

from __future__ import annotations

import json

ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MAX_TOKENS = 8192
JSON_MODE_INSTRUCTION = (
    "Return only a single valid JSON object as the entire answer. "
    "No prose, no markdown fences, no commentary."
)


class AnthropicWireError(RuntimeError):
    """The relay refused the request or returned an unusable stream."""


def _clean_messages(messages):
    """Split the game history into (system_text, anthropic_turns)."""
    system_parts = []
    turns = []
    for message in messages or []:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = message.get("content")
        if content is None:
            continue
        text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
        if not text.strip():
            continue
        if role in ("system", "developer"):
            system_parts.append(text)
            continue
        if role not in ("user", "assistant"):
            continue
        if turns and turns[-1]["role"] == role:
            turns[-1]["content"] += "\n\n" + text
        else:
            turns.append({"role": role, "content": text})
    # The wire requires the conversation to open with a user turn.
    while turns and turns[0]["role"] != "user":
        turns.pop(0)
    return "\n\n".join(system_parts), turns


def build_payload(messages, model, *, temperature=None, json_mode=True,
                  max_tokens=DEFAULT_MAX_TOKENS):
    system_text, turns = _clean_messages(messages)
    if json_mode:
        system_text = (system_text + "\n\n" + JSON_MODE_INSTRUCTION).strip()
    payload = {
        "model": model,
        "max_tokens": int(max_tokens),
        "messages": turns,
        "stream": True,
    }
    if system_text:
        payload["system"] = system_text
    if temperature is not None:
        # Anthropic accepts 0..1 only; a game callsite may ask for more.
        payload["temperature"] = max(0.0, min(1.0, float(temperature)))
    return payload


def _iter_events(response):
    """Yield (event_name, data_dict) from an Anthropic SSE stream."""
    event_name = None
    for raw_line in response.iter_lines():
        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else str(raw_line)
        if not line:
            event_name = None
            continue
        if line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
            continue
        if not line.startswith("data:"):
            continue
        data = line.split(":", 1)[1].strip()
        if not data or data == "[DONE]":
            continue
        try:
            parsed = json.loads(data)
        except ValueError:
            continue
        if isinstance(parsed, dict):
            yield event_name or parsed.get("type") or "", parsed


def stream_message(*, base_url, api_key, messages, model, headers=None,
                   temperature=None, json_mode=True, max_tokens=DEFAULT_MAX_TOKENS,
                   timeout=None, phase_emit=None):
    """One streamed Messages request, assembled into provider primitives.

    Returns ``{"text", "finish_reason", "usage", "id", "model"}`` where usage
    uses the OpenAI-compatible field names the rest of the game reads.
    """
    import httpx

    def phase(name, detail=None):
        if phase_emit is None:
            return
        try:
            phase_emit(name, detail) if detail else phase_emit(name)
        except Exception:
            pass

    url = "%s/v1/messages" % str(base_url).rstrip("/")
    request_headers = {
        "x-api-key": api_key,
        "Authorization": "Bearer %s" % api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
        "accept": "text/event-stream",
    }
    for key, value in (headers or {}).items():
        request_headers.setdefault(key, value)
    payload = build_payload(messages, model, temperature=temperature,
                            json_mode=json_mode, max_tokens=max_tokens)

    parts = []
    finish_reason = "stop"
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
             "cached_tokens": 0, "reasoning_tokens": 0}
    response_id = ""
    reported_model = model
    timeout_value = None if timeout is None else timeout

    phase("endpoint", "anthropic_messages")
    with httpx.Client(timeout=timeout_value) as client:
        with client.stream("POST", url, headers=request_headers, json=payload) as response:
            if response.status_code >= 400:
                body = response.read().decode("utf-8", "replace")
                raise AnthropicWireError(
                    "Anthropic wire refused the request (HTTP %s): %s"
                    % (response.status_code, body[:400])
                )
            phase("acknowledged")
            for event_name, event in _iter_events(response):
                kind = event.get("type") or event_name
                if kind == "message_start":
                    message = event.get("message") or {}
                    response_id = str(message.get("id") or "")
                    reported_model = str(message.get("model") or model)
                    start_usage = message.get("usage") or {}
                    usage["prompt_tokens"] = int(start_usage.get("input_tokens") or 0)
                    usage["cached_tokens"] = int(start_usage.get("cache_read_input_tokens") or 0)
                elif kind == "content_block_delta":
                    delta = event.get("delta") or {}
                    if delta.get("type") == "text_delta" and delta.get("text"):
                        parts.append(delta["text"])
                        phase("receiving")
                elif kind == "message_delta":
                    delta = event.get("delta") or {}
                    if delta.get("stop_reason"):
                        finish_reason = str(delta["stop_reason"])
                    delta_usage = event.get("usage") or {}
                    if delta_usage.get("output_tokens") is not None:
                        usage["completion_tokens"] = int(delta_usage["output_tokens"] or 0)
                    if delta_usage.get("input_tokens") is not None:
                        usage["prompt_tokens"] = int(delta_usage["input_tokens"] or 0)
                elif kind == "error":
                    detail = event.get("error") or {}
                    raise AnthropicWireError(
                        "Anthropic wire error: %s" % (detail.get("message") or detail or "unknown")
                    )

    usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
    text = "".join(parts)
    if not text.strip():
        raise AnthropicWireError("Anthropic wire returned no text")
    if finish_reason == "max_tokens":
        finish_reason = "length"
    return {
        "text": text,
        "finish_reason": finish_reason or "stop",
        "usage": usage,
        "id": response_id,
        "model": reported_model,
    }
