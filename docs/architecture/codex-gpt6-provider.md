# Codex GPT-6 provider

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

To set up: install the official Codex CLI, open Settings → AI Provider, select
Codex, and use **Sign in with ChatGPT** if needed. The device URL and temporary
code come from Codex. The interface shows account status, GPT-6 models and the
five-hour quota. `python utils/provider_health.py --provider codex` tests the
same cancellable route used by the game. Existing saved provider choices are
respected; switch to Codex explicitly on an existing installation.

OpenCode Go still uses the shared OpenAI-compatible endpoint client and its own
credential. Its model/effort profiles are independent of GPT-6, and its
`x-opencode-session` identity is created in the game owner process so provider
children inherit a stable session.

References: [Codex App Server](https://learn.chatgpt.com/docs/app-server),
[Codex authentication](https://learn.chatgpt.com/docs/auth),
[OpenCode Go](https://opencode.ai/docs/go/).
