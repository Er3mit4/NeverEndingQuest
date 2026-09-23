# Codex GPT-6 provider

This is a feature of the [Er3mit4 fork](../../FORK.md). The upstream Windows
installer clones `MoonlightByte/NeverEndingQuest` and does not install this
provider; use the fork checkout for the steps below.

`MODEL_PROVIDER=codex` uses the official Codex App Server over local stdio. The
Codex CLI owns the ChatGPT login, token refresh, model catalog and service quota.
NeverEndingQuest stores no Codex token or API key. The OpenAI API provider remains
an explicit, separately billed option.

The game cannot point its existing OpenAI-compatible custom endpoint directly
at Codex: App Server speaks its own JSON-RPC protocol rather than the Responses
or Chat Completions HTTP API. `core/ai/codex_client.py` is the adapter. It starts
one isolated ephemeral thread per completion, translates the ordered message
array and JSON schema, and returns the normal game completion shape through
`core/ai/api_client.py`. Each inference runs in an empty temporary directory
with read-only sandbox, tool features disabled, MCP servers disabled, and
incoming tool requests rejected. The live provider child owns cancellation;
Windows cancellation reaps its process tree.

The automatic GPT-6 matrix mirrors the prior task economics: Luna low for most
calls, Luna medium for T017 and the third T097 retry, Sol low for T026, T040,
T046, T084 and T099. Astra appears in the live model list but is never in an
automatic binding. The player may choose `gpt-6-astra` explicitly in Settings;
that saved choice overrides all Codex tasks until returned to Auto. The adapter
checks the current account's model and effort availability before each turn and
reports a quota or login failure without switching silently to the paid API.

## Setup and verification

1. Install the official Codex CLI and check `codex --version` from the same
   terminal or user account that launches the game. Start the fork checkout
   with `python run_web.py` (or `python run_web.py --ui legacy`).
2. Open Settings → AI Provider, select **Codex (GPT-6)**, and use **Sign in with
   ChatGPT** if disconnected. The device URL and temporary code come from the
   Codex CLI; do not paste a Codex token or `auth.json` into game settings.
3. Leave model choice on **Auto** for the economical task matrix. Selecting
   **GPT-6 Astra** is a persistent manual override for Codex tasks until the
   player returns to Auto. The panel reports account status, available GPT-6
   models and quota when the service supplies it.
4. Run `python utils/provider_health.py --provider codex` for a small real
   inference through the same cancellable route used by the game. It consumes
   part of the account's Codex quota. New installations default to Codex;
   existing saved provider choices are respected and require an explicit
   switch in Settings.

If the CLI is missing, put it on PATH and restart the game process. If login
expires, use Settings to sign in again. If a required model/effort is absent or
the quota is exhausted, the game reports that condition; select another
provider explicitly or wait for the quota to renew. There is no automatic
fallback to a billed OpenAI API call. Image generation and TTS remain separate
API features and may require their own credentials.

## Validation and limits

The implementation was validated on Windows with a connected ChatGPT Plus
account: a plain-text turn, JSON object, JSON schema, the real provider-health
child process, and 32 provider contract tests passed. The React build and a
provider-selection browser test passed. A full gameplay campaign and measured
quality comparison between Luna and Sol have not been run; the matrix keeps
the previous task-cost intent rather than claiming measured GPT-6 parity.

OpenCode Go still uses the shared OpenAI-compatible endpoint client and its own
credential. Its model/effort profiles are independent of GPT-6, and its
`x-opencode-session` identity is created in the game owner process so provider
children inherit a stable session.

References: [Codex App Server](https://learn.chatgpt.com/docs/app-server),
[Codex authentication](https://learn.chatgpt.com/docs/auth),
[OpenCode Go](https://opencode.ai/docs/go/).
