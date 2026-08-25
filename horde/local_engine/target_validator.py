import ipaddress
import re
from urllib.parse import urlparse


class TargetValidator:
    HOSTNAME_REGEX = re.compile(
        r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$"
    )
    DOMAIN_REGEX = re.compile(
        r"^(?=.{1,253}$)(?:(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$"
    )

    @staticmethod
    def validate(target: str, target_type: str) -> str:
        if not isinstance(target, str) or not target.strip():
            raise ValueError("Target must be a non-empty string.")

        target = target.strip()

        if target_type == "ipv4":
            try:
                addr = ipaddress.ip_address(target)
                if addr.version != 4:
                    raise ValueError("Target is not a valid IPv4 address.")
            except ValueError as exc:
                raise ValueError(f"Invalid IPv4 address format: {exc}") from exc

        elif target_type == "ipv6":
            try:
                addr = ipaddress.ip_address(target)
                if addr.version != 6:
                    raise ValueError("Target is not a valid IPv6 address.")
            except ValueError as exc:
                raise ValueError(f"Invalid IPv6 address format: {exc}") from exc

        elif target_type == "ip":
            try:
                ipaddress.ip_address(target)
            except ValueError as exc:
                raise ValueError(f"Invalid IP address format: {exc}") from exc

        elif target_type == "cidr":
            try:
                ipaddress.ip_network(target, strict=False)
            except ValueError as exc:
                raise ValueError(f"Invalid CIDR notation format: {exc}") from exc

        elif target_type == "hostname":
            if not TargetValidator.HOSTNAME_REGEX.match(target):
                raise ValueError("Invalid hostname format.")

        elif target_type == "domain":
            if not TargetValidator.DOMAIN_REGEX.match(target):
                raise ValueError("Invalid domain format.")

        elif target_type == "url":
            parsed = urlparse(target)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError(
                    "Invalid URL format. Must include http/https scheme and netloc."
                )

        else:
            raise ValueError(f"Unsupported target_type: {target_type}")

        return target
