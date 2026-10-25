# OpenCode Go Provider (DeepSeek V4.1 Flash)

Custom provider added to this fork on 2026-09-22. It routes every AI call
through [OpenCode Go](https://opencode.ai/en/docs/go) — OpenCode's low-cost
subscription that serves open models behind one relay — using the model the
player picks from the plan's catalogue (default **`deepseek-v4.1-flash`**).

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
- **Model**: one per player choice, applied to every call site (a plan
  subscription, not per-task billing). The default is
  `deepseek-v4.1-flash` ($0.15/$0.60 per 1M in/out off-peak, $0.30/$1.20
  peak; DeepSeek peak hours are 01:00–04:00 and 06:00–10:00 UTC Mon–Fri).
- **Catalogue**: discovered from `GET /zen/go/v1/models` when the service
  starts, cached in `user_settings.json` for 6 hours and refreshed by the
  Settings button. Without a usable key the plan's published list is shown
  instead, so the picker is never empty.
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

## Wire protocols per model

The relay publishes three protocols behind one base URL, so the model id
decides how a request travels (`utils/opencodego_models.transport_for`):

| Models | Wire | Base URL |
|---|---|---|
| `gpt-*`, `grok-*`, `muse-spark*` | OpenAI Responses | `/zen/go/v1` |
| `claude-*`, `qwen*`, `minimax-m3` | Anthropic Messages (`core/ai/anthropic_wire.py`) | `/zen/go` (SDK adds `/v1/messages`) |
| `gemini-*` | Google generateContent | not sent (unsupported here) |
| everything else | Chat Completions | `/zen/go/v1` |

## Reasoning-effort mapping

Only the contracts the relay documents are used, because one unsupported
level is a 400 on every call for that provider:

| Model family | Sent effort |
|---|---|
| `deepseek-v4*` | `low | high | max` (`none` becomes `low`) |
| `glm-5.2` | `high` or `max` (`low` is raised to `high`) |
| everything else | omitted — the relay's own default |

`_enforce_provider_constraints` still rewrites a stray
`reasoning_effort: "none"` to `low` for older compatibility profiles.
Temperature is accepted at every effort level and passes through like the
legacy/lmstudio providers. JSON mode follows the same default-ON contract as
the legacy path (opt-out with `response_format=None`); on the Anthropic wire,
which has no JSON flag, the contract is stated in the system prompt.

## Key files

| File | Change |
|---|---|
| `model_registry.py` | `opencodego` in `SUPPORTED_PROVIDERS`, independent `_GO_SPECIAL_LADDERS`, `deepseek-v4.1-flash` catalog entry |
| `model_config.py` | Go profiles and independent key persistence/detection helpers |
| `utils/openai_client.py` | Shared Local/Custom and Go compatible endpoint configuration; Go supplies its own URL, credential, JSON policy, headers and the transport for the chosen model |
| `utils/opencodego_models.py` | Plan catalogue discovery (`/zen/go/v1/models`), per-model transport routing, effort clamp, 6 h cache and the offline floor |
| `core/ai/anthropic_wire.py` | Anthropic Messages transport for the Go models that only exist on that wire |
| `utils/conversation_identity.py` | Conversation UUID created by the game owner and propagated to provider children |
| `core/ai/api_client.py` | Routes `opencodego` per model transport (chat / Responses / Anthropic), none→low effort constraint |
| `utils/provider_errors.py` | Player-facing display name "OpenCode Go" |
| `utils/openai_usage_tracker.py` | Known-provider telemetry set |
| `utils/startup_wizard.py`, `core/ai/effects_agent.py`, `core/npc/voice_service.py`, `core/npc/profile_service.py`, `core/generators/story_first/settings.py`, `core/generators/module_builder.py`, `utils/capture/live_provider_call.py`, `web/web_interface.py` | Explicit provider branches (config selection, key handlers, credentials check, T104/T105/T107 payload shapes) |
| `web/templates/game_interface.html`, `web/frontend/src/*` | Provider dropdown option, hint text, API-key section, plan model picker + socket contract (`get/set_opencodego_key`, `get_opencodego_models`, `refresh_opencodego_models`, `set_opencodego_model`) |
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
