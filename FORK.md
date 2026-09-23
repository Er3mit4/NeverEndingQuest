# ⚠️ Custom Fork — Experimental Provider & Mechanics Playground

This repository is a **fork of [MoonlightByte/NeverEndingQuest](https://github.com/MoonlightByte/NeverEndingQuest)**
maintained as an **experimental playground**. It exists to test **new AI
endpoints, providers and game mechanics** without touching the upstream project.
Behavior that proves stable here may inform upstream contributions later;
nothing here is a promise of upstream changes.

- **Upstream**: https://github.com/MoonlightByte/NeverEndingQuest (`origin` remote)
- **This fork**: https://github.com/Er3mit4/NeverEndingQuest (`fork` remote)
- **Base revision**: upstream `main` at `7b20bc8d` + the commits listed below

Everything not listed in [this fork's CHANGELOG entry](CHANGELOG.md) is
unchanged upstream code. The upstream README, licensing (Fair Source / SRD)
and architecture references all apply.

---

## What is implemented so far

### 1. Codex GPT-6 provider — `codex`

Text calls can use the official local Codex App Server with the player's
ChatGPT login and service quota. The game does not copy Codex credentials or
silently switch to the separately billed OpenAI API. New installations select
Codex by default; an existing saved provider choice remains in effect.

The task matrix preserves the previous economy: Luna low for most calls,
Luna medium for T017 and the last T097 retry, and Sol low for T026, T040,
T046, T084 and T099. **Astra is never chosen automatically**; the player can
select it explicitly in Settings and switch back to Auto. Account status,
available models and quota are visible in both players. Image and TTS features
still require their separate API services.

Full architecture and setup:
[docs/architecture/codex-gpt6-provider.md](docs/architecture/codex-gpt6-provider.md).

### 2. OpenCode Go provider — `opencodego` (DeepSeek V4.1 Flash)

A first-class AI provider that routes **every** call site (DM turns, combat
refereeing, validation, summaries, module generation, NPC systems…) through
[OpenCode Go](https://opencode.ai/en/docs/go) — OpenCode's $10/month
subscription that serves open models behind an OpenAI-compatible endpoint —
running **`deepseek-v4.1-flash`** everywhere.

- **Why this endpoint is interesting as a test bed**: OpenCode Go is an
  OpenAI-compatible *gateway* with gateway-specific requirements (session
  headers, client identification), reasoning tiers limited to
  `low | high | max`, and off-peak/peak pricing. Supporting it end-to-end is
  the template for wiring any future OpenAI-compatible third-party endpoint.
- Registry-integrated like the built-in providers: independent per-callsite
  ladders (`low`, `high`, `max`) preserved when the OpenAI matrix moved to GPT-6,
  streaming Chat Completions transport with the mandatory
  `x-opencode-session` / `User-Agent` headers.
- Key resolution: Settings-stored key → OpenCode CLI `auth.json`
  (auto-detected) → `config.py` override.
- Pricing in the model catalog: $0.15/$0.60 per 1M off-peak, $60/month limit.

Full architecture reference:
[docs/architecture/opencode-go-provider.md](docs/architecture/opencode-go-provider.md).

### 3. Startup character-commit convergence fix

DeepSeek's typographic output (em dashes, curly quotes) exposed a latent
defect in the startup wizard: the commit's write-then-read equality check
could never converge when a sheet contained characters that the read path
sanitizes, looping forever between "write pending" and a false "character
identity conflict". Fixed by normalizing model typography at the response
boundary and sanitizing before the commit's equality comparisons, plus a
deterministic code-level rejection of re-finalizing under a conflicted name.
Details in the [CHANGELOG](CHANGELOG.md) and
[startup-boot.md](docs/architecture/startup-boot.md).

### 4. Documentation

- [docs/architecture/opencode-go-provider.md](docs/architecture/opencode-go-provider.md) —
  provider reference (endpoint, headers, key resolution, effort mapping,
  validation performed, known limitations)
- [docs/architecture/codex-gpt6-provider.md](docs/architecture/codex-gpt6-provider.md) —
  ChatGPT login, model selection, quota and troubleshooting
- [docs/architecture/provider-routing.md](docs/architecture/provider-routing.md) —
  updated routing flow including the Go transport
- [CHANGELOG.md](CHANGELOG.md) — full custom-fork change entry

---

## Using it

```powershell
# 1. Install the official Codex CLI, then check that it is on PATH:
codex --version

# 2. Launch and choose Settings → AI Provider → Codex.
#    Sign in with ChatGPT there if needed; leave model choice on Auto.
.\launch_game.bat                 # React player (default)
.\launch_game.bat --ui legacy     # legacy player

# Optional: check the same Codex path used by the game:
python utils/provider_health.py --provider codex
```

OpenCode Go remains selectable in Settings and can reuse the credential
stored by the OpenCode CLI or a key supplied in the provider panel.

The provider selection persists in `user_settings.json` (gitignored). No
secrets are committed; `config.py` and `user_settings.json` stay out of the
repository by design.

## Sync policy

```bash
git pull origin main     # bring upstream changes in
git push fork main       # push fork work
```

Runtime game data (`save_games/`, `data/companion_memories/`, captures, logs,
`config.py`, `user_settings.json`) is local-only and never pushed. Fork commits
touch code, UI and docs only.

## Candidate experiments (roadmap)

Ideas queued for this playground, not yet implemented:

- **More third-party endpoints** via the OpenCode Go adapter pattern:
  DeepSeek V4 Pro, GLM-5.x, Kimi K2.x, Qwen3.x, MiniMax — all served by the
  same Go gateway, selectable per call-site tier.
- **Per-callsite model routing across Go gateway models** (e.g. a cheaper
  flash model for utility calls and a stronger open model for the DM loop),
  measured against the current GPT-6 task matrix.
- **Effort-tier capture evaluation** for the DeepSeek rungs, mirroring the
  upstream blind quality/cost methodology
  (`utils/provider_health.py --provider opencodego` as the entry point).
- **Game mechanics**: to be explored after the provider layer stabilizes.

---

> Upstream project: **NeverEndingQuest** by MoonlightByte — an AI-powered
> Dungeon Master for SRD 5.2.1 tabletop campaigns. All credit for the
> original engine belongs to the upstream maintainers; this fork documents
> only what it changes on top.
