# OpenCode Go Provider (DeepSeek V4.1 Flash)

Custom provider added to this fork on 2026-09-22. It routes every AI call
through [OpenCode Go](https://opencode.ai/en/docs/go) — OpenCode's low-cost
subscription ($10/month) that serves open models behind an OpenAI-compatible
endpoint — using **`deepseek-v4.1-flash`** as the model for all call sites.

> This is a **custom fork feature**, not part of upstream NeverEndingQuest.
> Upstream supports `openai`, `gemini`, `legacy` and `lmstudio`; this fork adds
> `opencodego` as a first-class provider with the same per-callsite registry
> machinery. See [provider-routing.md](provider-routing.md) for the shared
> routing flow this provider plugs into.

## Overview

```
NeverEndingQuest ──(OpenAI SDK, Chat Completions streaming)──▶
    https://opencode.ai/zen/go/v1/chat/completions   (Bearer auth)
```

- **Provider id**: `opencodego` (`MODEL_PROVIDER` option, switchable in
  Settings → AI Provider on both players; persists in `user_settings.json`)
- **Model**: `deepseek-v4.1-flash` for every call site — $0.15/$0.60 per 1M
  in/out off-peak ($0.30/$1.20 peak; DeepSeek peak hours are 01:00–04:00 and
  06:00–10:00 UTC Mon–Fri), cached read $0.003, $60/month usage limit.
- **Transport**: streaming Chat Completions via the standard `openai` SDK
  (`_chat_stream_completion`). The Go endpoint has **no** Responses surface for
  this model, so the provider never uses the OpenAI Responses path.

## Mandatory gateway headers

OpenCode Go requires two extra headers on every request
(docs/go/#where-can-i-use-it), set in `utils/openai_client.py`:

| Header | Value | Purpose |
|---|---|---|
| `x-opencode-session` | UUID created by the game owner for the current conversation and inherited by provider children | Keeps retries and subprocess calls in one conversation while a new game can start a new session. |
| `User-Agent` | `NeverEndingQuest/1.0` | The client must identify itself by name, never as a generic SDK user agent |

Without the session header the gateway rejects the request with
`400 MissingSessionID`.

## API key resolution

`model_config.get_opencodego_key()` resolves the key in priority order:

1. A key saved in the web UI (`get/set_opencodego_key` socket events →
   `persist_opencodego_key`, stored in the OS credential store or the
   owner-only `user_settings.json` JSON fallback)
2. The `opencode-go` entry the **OpenCode CLI** persists at
   `%USERPROFILE%\.local\share\opencode\auth.json` (auto-detected — no copy
   needed if you already subscribe through the CLI)
3. A live `config.OPENCODEGO_API_KEY` override from `config.py`
   (placeholder `your_opencodego_api_key_here` is ignored)

The key is read live per call, so a Settings change applies on the next
request without a restart.

## Reasoning-effort mapping

DeepSeek V4.1 Flash supports reasoning efforts **`low | high | max` only**
(no `none`). The Go ladder is now explicit and independent of the OpenAI/Codex
GPT-6 matrix. The earlier effective choices were preserved:

| Task | Go ladder |
|---|---|
| Most call sites | `low` |
| T017 | `high` |
| T026 | `max` |
| T097 retries | `low`, `low`, `high` |

`_enforce_provider_constraints` still rewrites a stray
`reasoning_effort: "none"` to `low` for older compatibility profiles.
Temperature is accepted at every effort level and passes through like the
legacy/lmstudio providers. JSON mode follows the same default-ON contract as
the legacy path (opt-out with `response_format=None`).

## Key files

| File | Change |
|---|---|
| `model_registry.py` | `opencodego` in `SUPPORTED_PROVIDERS`, independent `_GO_SPECIAL_LADDERS`, `deepseek-v4.1-flash` catalog entry |
| `model_config.py` | Go profiles and independent key persistence/detection helpers |
| `utils/openai_client.py` | Shared Local/Custom and Go compatible endpoint configuration; Go supplies its own URL, credential, JSON policy and headers |
| `utils/conversation_identity.py` | Conversation UUID created by the game owner and propagated to provider children |
| `core/ai/api_client.py` | Routes `opencodego` through the Chat Completions adapter (`_opencodego_call_kwargs`), none→low effort constraint |
| `utils/provider_errors.py` | Player-facing display name "OpenCode Go" |
| `utils/openai_usage_tracker.py` | Known-provider telemetry set |
| `utils/startup_wizard.py`, `core/ai/effects_agent.py`, `core/npc/voice_service.py`, `core/npc/profile_service.py`, `core/generators/story_first/settings.py`, `core/generators/module_builder.py`, `utils/capture/live_provider_call.py`, `web/web_interface.py` | Explicit provider branches (config selection, key handlers, credentials check, T104/T105/T107 payload shapes) |
| `web/templates/game_interface.html`, `web/frontend/src/*` | Provider dropdown option, hint text, API-key section + socket contract (`get/set_opencodego_key`, `opencodego_key_status`) |
| `config.py` / `config_template.py` | `OPENCODEGO_API_KEY` placeholder |

## Validation performed (2026-09-22)

- Real end-to-end call against `https://opencode.ai/zen/go/v1`: plain text,
  `json_object` mode, and reasoning `low`/`high` all return normalized
  OpenAI-shaped responses with usage accounting.
- Full production boundary: `capture_and_fanout("T013"/"T082", ...)` with
  `_request_provider='opencodego'` resolves the registry ladder to
  `deepseek-v4.1-flash` and completes.
- `validate_model_registry()` passes with the provider in
  `SUPPORTED_PROVIDERS`; the current `provider_contract_test.py` passes all
  32 tests when run with the project's dependencies and pytest available.
- React frontend `tsc -b && vite build` passes; vitest suite at its baseline.

## Known limitations

- **Quality of Go reasoning tiers**: the preserved `low`/`high`/`max` matrix
  has not undergone a new gameplay comparison since the GPT-6 migration.
  Use `utils/provider_health.py --provider opencodego` to check live transport,
  then representative gameplay to assess quality.
- **TTS and image generation** remain OpenAI-only features (DALL·E / tts-1
  endpoints do not exist on the Go gateway); they keep using
  `config.OPENAI_API_KEY` regardless of the selected provider.
- **DeepSeek peak hours** double token prices (01:00–04:00 and 06:00–10:00
  UTC Mon–Fri).
