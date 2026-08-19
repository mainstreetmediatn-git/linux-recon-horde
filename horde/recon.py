from __future__ import annotations

import socket
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

from .models import Evidence


@dataclass(slots=True)
class ScopePolicy:
    allowed_hosts: set[str]

    def require_allowed(self, host: str) -> None:
        if host not in self.allowed_hosts:
            raise PermissionError(f"target outside authorized scope: {host}")


def dns_lookup(host: str, *, policy: ScopePolicy) -> Evidence:
    policy.require_allowed(host)
    addresses = sorted({item[4][0] for item in socket.getaddrinfo(host, None)})
    return Evidence(
        evidence_id=f"dns:{host}",
        target=host,
        source="socket.getaddrinfo",
        observed_at=datetime.now(timezone.utc).isoformat(),
        observation=", ".join(addresses),
        confidence=1.0 if addresses else 0.0,
        metadata={"addresses": addresses},
    )


def tls_certificate_summary(host: str, *, policy: ScopePolicy, port: int = 443, timeout: float = 5.0) -> Evidence:
    policy.require_allowed(host)
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as raw:
        with context.wrap_socket(raw, server_hostname=host) as wrapped:
            cert = wrapped.getpeercert()
    subject = dict(x[0] for x in cert.get("subject", []))
    issuer = dict(x[0] for x in cert.get("issuer", []))
    summary = {
        "common_name": subject.get("commonName"),
        "issuer": issuer.get("commonName"),
        "not_before": cert.get("notBefore"),
        "not_after": cert.get("notAfter"),
    }
    return Evidence(
        evidence_id=f"tls:{host}:{port}",
        target=host,
        source="python.ssl",
        observed_at=datetime.now(timezone.utc).isoformat(),
        observation=str(summary),
        confidence=1.0,
        metadata=summary,
    )


def inspect_http_headers(url: str, headers: dict[str, str]) -> list[dict[str, str]]:
    """Passive analysis only; this function never sends traffic."""
    host = urlparse(url).hostname or ""
    normalized = {k.lower(): v for k, v in headers.items()}
    findings: list[dict[str, str]] = []
    checks = {
        "strict-transport-security": "Missing HSTS header",
        "content-security-policy": "Missing Content-Security-Policy header",
        "x-content-type-options": "Missing X-Content-Type-Options header",
    }
    for header, title in checks.items():
        if header not in normalized:
            findings.append({"target": host, "severity": "info", "title": title})
    return findings
