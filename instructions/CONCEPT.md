# Concept of the Horde

Linux Recon Horde is a constitution-governed, multi-agent reconnaissance and security-assessment framework for systems the operator owns or is explicitly authorized to assess.

The Horde is not intended to be a single monolithic scanner. It is a coordinated society of specialist agents, judges, auditors, memory services, evidence services, managed execution environments, and human approval gates.

## Core operating model

A typical Horde engagement follows this flow:

1. A human creates or approves an engagement and target scope.
2. A mission contract defines objective, allowed targets, constraints, participants, evidence requirements, approved tools, approval gates, and reporting requirements.
3. Specialist agents perform bounded tasks appropriate to their role.
4. Every useful observation becomes structured evidence with provenance, source, timestamp, target, confidence, and metadata.
5. Judge agents correlate evidence, detect contradictions, suppress duplicates, score confidence, and route uncertain findings to human review.
6. Auditor functions inspect lifecycle, policy, tool use, approvals, evidence handling, and important state changes.
7. Memory records preserve validated knowledge without silently overwriting contested or superseded information.
8. Reports are generated from evidence and judged findings, not unsupported assertions.
9. Agents are evaluated over a lifecycle. Aging, degraded, obsolete, or poorly performing agents enter succession rather than disappearing abruptly.
10. Successors train in probation/shadow mode, inherit only approved knowledge, pass readiness gates, overlap with predecessors, and require human approval before taking over.

## Intended specialist roles

The architecture is designed to support specialists such as:

- DNS and hostname intelligence
- TLS/certificate inspection
- HTTP metadata, title, header, cookie, and security-header analysis
- technology fingerprinting
- approved content/route discovery from observed application structure
- subdomain/public metadata discovery
- bounded TCP/service metadata collection in approved environments
- bounded UDP/service checks with explicit load policies
- version detection
- managed tool adapters
- evidence normalization
- Judge and Auditor roles

## Enterprise direction

The target product is a serious operator platform with:

- engagements and authorization records
- workspaces and RBAC
- target inventory and site maps
- HTTP history/request inspection and safe replay workflows
- passive scanner findings
- findings/evidence/report management
- multi-agent orchestration
- agent lifecycle and succession
- managed Python/Go/Rust/Bash/container environments
- tool/package health
- interface/wireless capability visibility
- VPN/tunnel/approved engagement connectivity profiles
- hardware/runtime diagnostics
- versioned constitution and policy enforcement
- append-only audit trails
- dashboard and operator console

## Non-goals and boundaries

The Horde must not become a platform for credential theft, uncontrolled brute force, malware delivery, persistence, destructive actions, anti-forensics, trace wiping, or unsafe external targeting.

High-impact actions require explicit human control. Recon remains engagement-scoped and authorization-gated.
