from __future__ import annotations

import argparse
import json

from .recon import ScopePolicy, dns_lookup, tls_certificate_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="horde", description="Authorized Linux Recon Horde CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    dns = sub.add_parser("dns", help="Resolve an explicitly authorized host")
    dns.add_argument("host")

    tls = sub.add_parser("tls", help="Inspect the TLS certificate of an explicitly authorized host")
    tls.add_argument("host")
    tls.add_argument("--port", type=int, default=443)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    policy = ScopePolicy({args.host})

    if args.command == "dns":
        result = dns_lookup(args.host, policy=policy)
    else:
        result = tls_certificate_summary(args.host, policy=policy, port=args.port)

    print(json.dumps({
        "evidence_id": result.evidence_id,
        "target": result.target,
        "source": result.source,
        "observed_at": result.observed_at,
        "observation": result.observation,
        "confidence": result.confidence,
        "metadata": result.metadata,
    }, indent=2))


if __name__ == "__main__":
    main()
