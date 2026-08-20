"""Target normalization shared by every execution path."""

from dataclasses import dataclass
from ipaddress import ip_address
from urllib.parse import urlsplit


@dataclass(frozen=True)
class NormalizedTarget:
    original: str
    host: str
    path: str
    scheme: str | None
    ip: object | None
    canonical: str


def normalize_target(value: str) -> NormalizedTarget:
    raw = value.strip()
    if not raw or any(ord(char) < 32 for char in raw):
        raise ValueError("target is empty or contains control characters")
    # urlsplit treats an unbracketed IPv6 literal as a malformed hostname
    # fragment. Bracket it only for parsing; the normalized host remains bare.
    try:
        raw_ip = ip_address(raw)
    except ValueError:
        raw_ip = None
    candidate = raw if "://" in raw else f"//[{raw}]" if raw_ip and raw_ip.version == 6 else f"//{raw}"
    parsed = urlsplit(candidate)
    if not parsed.hostname:
        raise ValueError("target has no hostname")
    try:
        host = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError("target hostname is not a valid IDN") from exc
    try:
        parsed_ip = ip_address(host)
    except ValueError:
        parsed_ip = None
    path = parsed.path or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    scheme = parsed.scheme.lower() if parsed.scheme else None
    canonical_host = f"[{host}]" if parsed_ip and parsed_ip.version == 6 else host
    canonical = f"{scheme + '://' if scheme else ''}{canonical_host}{path}"
    return NormalizedTarget(raw, host, path, scheme, parsed_ip, canonical)
