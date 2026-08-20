from horde.config import Settings


def test_tool_allowlist_accepts_comma_separated_environment_value(monkeypatch):
    monkeypatch.setenv("HORDE_TOOL_ALLOWLIST", "dns, http, tls")
    settings = Settings(_env_file=None)
    assert settings.tool_allowlist == ["dns", "http", "tls"]
