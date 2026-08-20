# Current State — Confirmed Implementation

This document describes the code that is actually present on the `recovered-architecture` branch. It should be updated whenever a major subsystem becomes real.

## Project/package foundation

Implemented:

- installable Python package configuration in `pyproject.toml`
- `horde` Python package
- GitHub Actions pytest workflow
- unit tests under `tests/`
- architecture and roadmap documentation
- `.gitignore` and `.env.example`

## Domain model

Implemented in `horde/models.py`:

- `AgentState`
- `MemoryState`
- `Evidence`
- `MemoryRecord`
- `Agent`
- `MissionContract`

Agent records already include identity, role, specialization, state, trust, reputation, health, tenure, memory namespaces, allowed tools, scopes, environment assignment, predecessor/successor lineage, evidence quality, compliance score, and mission history.

## Agent lifecycle and succession

Implemented in `horde/lifecycle.py`:

- agent proposal
- human-gated admission
- Judge/Auditor-gated activation
- suspension
- successor-trigger evaluation based on tenure, health, or quality
- successor creation and predecessor lineage
- successor-training state
- prevention of retirement until a successor is active
- Judge/Auditor/human-gated handoff
- controlled approved-memory handoff
- retirement and archive transitions
- in-process audit event creation

Current limitation: lifecycle manager state is still primarily in-memory unless a higher service layer explicitly persists it.

## Recon layer

Implemented in `horde/recon.py`:

- explicit scope policy
- DNS lookup for an approved host
- TLS certificate summary for an approved host
- passive HTTP security-header inspection without sending traffic

The recon layer is intentionally narrow today.

## Durable persistence

Implemented in `horde/storage.py`:

- SQLite-backed record storage
- WAL mode and foreign-key enablement
- durable agents
- durable missions
- durable evidence
- durable memory
- append-only-style audit-event table
- engagement metadata
- managed-environment metadata
- database reopen/restart tests

Important: persistence exists as a storage service, but not every lifecycle/orchestration path is wired through it yet.

## Constitutional policy engine

Implemented in `horde/policy.py`:

- explicit allow/deny/require-approval decisions
- deny-by-default mission checks
- explicit mission authorization requirement
- required target scope
- required evidence contract
- agent/tool/target scope enforcement
- lifecycle approval rules
- separation-of-powers validation

## Orchestration

Implemented in `horde/orchestration.py`:

- policy-gated job preparation
- mission participant validation
- mission tool validation
- target-scope validation
- bounded evidence-producing job execution
- blocked/running/complete/failed states

Current limitation: this is an orchestration kernel, not yet a long-running queue/worker system.

## Judging

Implemented in `horde/judging.py`:

- evidence correlation
- confidence averaging
- multi-source corroboration
- contested evidence state for target inconsistency
- low-confidence human-review routing
- duplicate finding suppression

Current limitation: Judge output is not yet durably persisted or connected to a complete findings service.

## Tests currently present

Confirmed test areas include:

- human approval required for admission
- retirement blocked until successor is active
- successor triggers from lifecycle health/tenure/quality
- out-of-scope target denial
- passive HTTP-header checks
- SQLite persistence across reopen
- durable engagement/environment metadata
- constitutional mission denial
- tool/target admission checks
- lifecycle approval requirements
- separation-of-powers rejection

## UI / Replit status

A separate Replit app has been used to develop the enterprise operator-console UI and product concept. It should not be assumed to be the source of truth for backend completion until its implementation has been verified and synchronized into this repository.

The GitHub repository remains the durable engineering source of truth for confirmed Horde code.
