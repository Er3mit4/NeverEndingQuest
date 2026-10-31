"""The OpenCode Go bridge exposes the same model and ladders as before."""

from __future__ import annotations


def test_bridge_keeps_the_default_model_and_ladders():
    from fork_ext.providers.opencodego import SPEC

    assert SPEC.name == "opencodego"
    assert SPEC.provider_models == {
        "full": "deepseek-v4.1-flash",
        "mini": "deepseek-v4.1-flash",
    }
    assert SPEC.default_ladder == ("OPENCODEGO_LOW",)
    assert SPEC.ladder_for("T017") == ("OPENCODEGO_HIGH",)
    assert SPEC.ladder_for("T026") == ("OPENCODEGO_MAX",)
    assert SPEC.ladder_for("T097") == (
        "OPENCODEGO_LOW", "OPENCODEGO_LOW", "OPENCODEGO_HIGH")
    assert SPEC.ladder_for("T067") == ("OPENCODEGO_LOW",)
    for name in ("OPENCODEGO_LOW", "OPENCODEGO_HIGH", "OPENCODEGO_MAX"):
        assert SPEC.profiles[name]["model"] == "deepseek-v4.1-flash"


def test_bridge_installs_into_the_game_registries():
    import model_config
    import model_registry

    assert "opencodego" in model_config.PROVIDER_MODELS
    assert "opencodego" in model_registry.SUPPORTED_PROVIDERS
    assert model_config.resolve_callsite_config("T026", "opencodego") == {
        "model": "deepseek-v4.1-flash", "reasoning_effort": "max"}
    assert model_config.resolve_callsite_config("T097", "opencodego", 2) == {
        "model": "deepseek-v4.1-flash", "reasoning_effort": "high"}


def test_bridge_connection_is_openai_compatible_chat_by_default():
    from utils.openai_client import compatible_connection, is_compatible_provider

    assert is_compatible_provider("opencodego") is True
    connection = compatible_connection("opencodego")
    assert connection["model"] == "deepseek-v4.1-flash"
    assert connection["base_url"] == "https://opencode.ai/zen/go/v1"
    assert connection["transport"] == "chat"
    assert connection["json_object"] is True
    assert connection["headers"]["User-Agent"] == "NeverEndingQuest/1.0"
    assert callable(connection["effort_normalizer"])


def test_bridge_effort_normalizer_follows_the_plan_contract():
    from fork_ext.opencodego import catalog

    assert catalog.adjust_reasoning_effort("deepseek-v4.1-flash", "none") == "low"
    assert catalog.adjust_reasoning_effort("deepseek-v4.1-flash", "max") == "max"
    assert catalog.adjust_reasoning_effort("glm-5.2", "low") == "high"
    assert catalog.adjust_reasoning_effort("kimi-k3", "high") is None
