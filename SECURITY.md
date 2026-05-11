# Security Policy

GovernSpec is a local-first compiler and validation tool for AI task contracts. It is
not a runtime sandbox or enforcement system.

## Supported Versions

Security fixes are currently accepted for the latest `0.1.x` release line.

## Reporting a Vulnerability

Please report suspected vulnerabilities privately to `research@symboliclight.com`.
Include:

- affected version or commit,
- operating system and Python version,
- minimal reproduction steps,
- expected and observed behavior,
- any security impact you believe is possible.

Do not include real secrets, API keys, customer data, or private prompts in reports.

## Security Boundaries

GovernSpec can describe permissions, compile instruction artifacts, and run offline
acceptance checks. It cannot guarantee that a downstream model, editor, or agent
runtime will obey those instructions at execution time.
