from horde.recon import ScopePolicy, inspect_http_headers


def test_scope_policy_denies_unknown_target():
    policy = ScopePolicy({"lab.local"})
    try:
        policy.require_allowed("outside.example")
    except PermissionError:
        pass
    else:
        raise AssertionError("out-of-scope target should be denied")


def test_passive_header_analysis_does_not_require_network():
    findings = inspect_http_headers(
        "https://lab.local/",
        {"Server": "demo", "X-Content-Type-Options": "nosniff"},
    )
    titles = {item["title"] for item in findings}
    assert "Missing HSTS header" in titles
    assert "Missing Content-Security-Policy header" in titles
    assert "Missing X-Content-Type-Options header" not in titles
