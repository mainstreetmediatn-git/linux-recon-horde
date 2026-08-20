# Linux Recon Horde

**Linux Recon Horde** is a specialist reconnaissance and judging framework for **owned systems, approved labs, and explicitly authorized security assessments**.

Rather than treating reconnaissance as one monolithic scan, Horde is designed as a panel: specialist agents collect and interpret evidence, judges compare findings and contradictions, memory preserves prior context, and the human operator remains the final authority.

## Core idea

Horde separates work into distinct capability families:

- **Core** — orchestration, scope, policy, job lifecycle, audit trail
- **Agents** — specialist recon workers
- **Judges** — compare evidence, confidence, conflicts, and conclusions
- **Skills** — reusable analysis capabilities
- **Tools** — controlled integrations with approved Linux utilities
- **Memory** — prior findings and related context
- **Evidence** — source, timestamp, command/tool provenance, raw and normalized observations
- **Reports** — operator-readable findings and exports
- **Config** — safe defaults, target scope, rate/load controls, feature gates

Recovered project references also identify planned entry points such as `horde_cli.py`, `horde_scanner.py`, and `phased_scanner.py`.

## Recovered specialist capabilities

The original design references specialist coverage for:

- TCP and UDP service discovery
- Version detection
- Controlled script execution
- HTTP title checks
- Web fingerprinting
- DNS lookup
- TLS inspection
- Subdomain lookup
- Judge-based review of findings

## Safety model

Horde is intentionally scoped for defensive and authorized use.

- Require explicit authorization and target scope.
- Default to passive or low-impact reconnaissance where possible.
- Reduce UDP load and avoid unnecessary high-noise probing.
- Disable OS fingerprinting when it is not appropriate for the engagement.
- Preserve evidence and reports for operator review.
- Do not perform credential attacks, exploitation, persistence, destructive actions, or unsafe external targeting.

## Operator relationship

Horde is a **specialist secondary-opinion and judge layer**. It is separate from SentinalOS and any other primary operator/runtime. The human operator remains the final authority over scope, execution, interpretation, and action.

## Lab stack

The recovered project notes reference a Linux security lab built around Kali, Nmap, Tshark, Nginx, Express, curl, OpenSSL, dig, and Python virtual environments.

## Project status

The GitHub repository was recovered as an almost-empty shell. Architecture and capability notes are being reconstructed from the project vault before implementation begins.

See `docs/ARCHITECTURE.md` and `docs/ROADMAP.md` for the recovered design and build sequence.
