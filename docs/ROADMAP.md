# Roadmap

## Phase 0 — Recovery and safety lock

- Preserve recovered architecture and project boundaries.
- Define explicit authorization/scope model.
- Establish evidence provenance schema and audit trail.
- Add representative demo data and test fixtures only.

## Phase 1 — Core domain model

- Engagements and approved targets
- Recon jobs and phases
- Specialists and judge identities
- Evidence and normalized observations
- Findings, confidence, contradictions, and status
- Reports and activity history

## Phase 2 — Passive-first specialists

- DNS lookup
- TLS inspection
- HTTP title/header analysis
- Web technology fingerprinting
- Public subdomain discovery using approved sources

Every specialist should emit structured evidence rather than opaque text.

## Phase 3 — Controlled network-lab specialists

For owned/approved lab targets only:

- TCP service discovery
- Carefully bounded UDP discovery
- Version detection
- Controlled scanner/script adapters

Add rate/load policies and operator-visible execution plans before actions run.

## Phase 4 — Judge layer

- Evidence correlation
- Duplicate suppression
- Confidence scoring
- Contradiction detection
- Freshness checks
- Independent specialist comparison
- Human-review queue for uncertain conclusions

## Phase 5 — Memory and change detection

- Historical engagement memory
- Known false-positive memory
- Compare current evidence to previous evidence
- Surface meaningful target changes

## Phase 6 — Operator experience

- Command-center dashboard
- Asset inventory
- Recon queue and phase view
- Agent/judge panel
- Evidence explorer
- Findings and contradiction review
- Timeline and audit log
- Exportable reports

## Phase 7 — Quality bar

- Tests for scope enforcement and evidence traceability
- Safe default configuration
- Reproducible demo environment
- Clear contributor docs
- Architecture diagrams
- Screenshots/demo GIFs
- Issue templates and contribution workflow

The goal is a project that is useful, explainable, safe by default, and visually compelling enough to earn attention because of its architecture—not because it promises indiscriminate scanning.
