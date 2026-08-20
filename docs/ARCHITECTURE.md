# Recovered Architecture

## Purpose

Linux Recon Horde is a multi-specialist reconnaissance framework for authorized security work. Its defining feature is not simply tool execution; it is structured disagreement, evidence comparison, and judge-assisted synthesis.

## Major layers

### Core
Responsible for engagement scope, authorization state, orchestration, job lifecycle, rate/load policy, audit logging, and safe execution gates.

### Agents
Specialists should operate independently enough to produce useful second opinions. Recovered capability areas include network service discovery, version detection, HTTP analysis, web fingerprinting, DNS, TLS, subdomain discovery, and controlled script-based checks.

### Judges
Judges evaluate agent outputs rather than blindly accepting them. A judge should compare evidence provenance, confidence, contradictions, duplicate observations, freshness, and whether a conclusion is sufficiently supported.

### Skills and tools
Skills represent reusable analysis behavior. Tools are concrete controlled integrations with approved Linux utilities and libraries. Tool access should be scoped, auditable, and policy-gated.

### Memory
Memory stores prior approved-target context, previous findings, known false positives, historical evidence, and related engagements so agents can avoid needless repetition and identify meaningful changes.

### Evidence
Every meaningful observation should preserve provenance: target, time, specialist, tool/check, raw observation reference, normalized observation, and confidence. Conclusions should remain traceable back to evidence.

### Reports
Reports synthesize findings for a human operator. They should distinguish observations from interpretations, expose disagreements when unresolved, and retain enough provenance to reproduce or review a conclusion.

### Config
Configuration owns scope, safe defaults, rate/load limits, enabled specialists, approved integrations, environment settings, and feature gates.

## Entry-point concepts recovered from project notes

- `horde_cli.py`
- `horde_scanner.py`
- `phased_scanner.py`

These names are preserved as historical design references; implementation may evolve while retaining their intended responsibilities.

## Recovered lab/tool ecosystem

Project notes reference Kali, Nmap, Tshark, Nginx, Express, curl, OpenSSL, dig, and Python virtual environments.

## Boundary with SentinalOS

SentinalOS is a separate primary operator/runtime. Horde must not absorb or silently depend on it. Horde acts as a specialist secondary-opinion/judge layer, and the human remains final authority.

## Safety invariants

1. Only owned or explicitly authorized targets are in scope.
2. Scope must be explicit and reviewable.
3. Passive/low-impact methods are preferred where practical.
4. UDP load is constrained.
5. OS fingerprinting can be disabled when inappropriate.
6. Evidence and reports are preserved.
7. No credential attacks, exploitation, persistence, destructive behavior, or unsafe external targeting are part of the default product.
