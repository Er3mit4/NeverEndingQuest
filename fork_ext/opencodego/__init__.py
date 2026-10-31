"""OpenCode Go provider bridge for this fork.

Everything specific to the OpenCode Go provider lives under this package. The
game reaches it through four small, marked hooks (see ``registry``):

* ``model_registry``  -- provider names and per-callsite ladders
* ``model_config``    -- profile dicts, provider entry and the persisted key
* ``utils.openai_client`` -- the OpenAI-compatible connection
* ``core.ai.api_client``  -- constraints, effort mapping and wire transport

Upstream files never import provider internals: they ask this package, and an
upstream-only checkout (no ``fork_ext``) simply runs the built-in providers.
"""
