# ⚠️ Custom Fork — Experimental Provider & Mechanics Playground

This repository is a **fork of [MoonlightByte/NeverEndingQuest](https://github.com/MoonlightByte/NeverEndingQuest)**
maintained as a **private experimental playground**. It exists to test **new AI
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

### 1. OpenCode Go provider — `opencodego` (DeepSeek V4.1 Flash)

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
- Registry-integrated like the built-in providers: per-callsite ladders,
  effort rung translation (`none→low`, `medium→high`, `high→max`),
  streaming Chat Completions transport with the mandatory
  `x-opencode-session` / `User-Agent` headers.
- Key resolution: Settings-stored key → OpenCode CLI `auth.json`
  (auto-detected) → `config.py` override.
- Pricing in the model catalog: $0.15/$0.60 per 1M off-peak, $60/month limit.

Full architecture reference:
[docs/architecture/opencode-go-provider.md](docs/architecture/opencode-go-provider.md).

### 2. Startup character-commit convergence fix

DeepSeek's typographic output (em dashes, curly quotes) exposed a latent
defect in the startup wizard: the commit's write-then-read equality check
could never converge when a sheet contained characters that the read path
sanitizes, looping forever between "write pending" and a false "character
identity conflict". Fixed by normalizing model typography at the response
boundary and sanitizing before the commit's equality comparisons, plus a
deterministic code-level rejection of re-finalizing under a conflicted name.
Details in the [CHANGELOG](CHANGELOG.md) and
[startup-boot.md](docs/architecture/startup-boot.md).

### 3. Documentation

- [docs/architecture/opencode-go-provider.md](docs/architecture/opencode-go-provider.md) —
  provider reference (endpoint, headers, key resolution, effort mapping,
  validation performed, known limitations)
- [docs/architecture/provider-routing.md](docs/architecture/provider-routing.md) —
  updated routing flow including the Go transport
- [CHANGELOG.md](CHANGELOG.md) — full custom-fork change entry

---

## Using it

```powershell
# 1. Configure (optional if you already use the OpenCode CLI):
#    Settings → AI Provider → OpenCode Go → paste your Go key, or let the
#    auto-detection pick it up from the OpenCode CLI auth.json.

# 2. Launch
launch_game.bat                 # React player (default)
launch_game.bat --ui legacy     # legacy player
```

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
- **Per-callsite model routing across gateways** (e.g. cheap flash model for
  micro utility calls, stronger open model for the DM loop) measured against
  the upstream GPT-5.x matrix.
- **Effort-tier capture evaluation** for the DeepSeek rungs, mirroring the
  upstream blind quality/cost methodology
  (`utils/provider_health.py --provider opencodego` as the entry point).
- **Game mechanics**: to be explored after the provider layer stabilizes.

---

> Upstream project: **NeverEndingQuest** by MoonlightByte — an AI-powered
> Dungeon Master for SRD 5.2.1 tabletop campaigns. All credit for the
> original engine belongs to the upstream maintainers; this fork documents
> only what it changes on top.
