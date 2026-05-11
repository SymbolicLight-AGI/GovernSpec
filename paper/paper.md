---
title: "GovernSpec: Contract compilation and offline acceptance testing for AI agent artifacts"
tags:
  - Python
  - software engineering
  - AI agents
  - structured outputs
  - task contracts
authors:
  - name: Ting Liu
    affiliation: 1
affiliations:
  - name: SymbolicLight Research, China
    index: 1
date: 24 April 2026
bibliography: paper.bib
---

# Summary

GovernSpec is a local-first command-line tool and Python library for describing AI
agent tasks as explicit, reviewable contracts. A contract records the task goal,
permissions, constraints, required human confirmation gates, expected output shape,
and deterministic acceptance checks. GovernSpec validates this source contract,
normalizes it into an intermediate intent representation, compiles it into
tool-specific artifacts, imports existing artifacts back into draft contracts, and
tests generated outputs offline.

The current implementation supports instruction-style targets such as `AGENTS.md`,
Claude-style project memory, Cursor project rules, structured-output payloads for
JSON-schema-based API workflows, and an MCP-oriented plan artifact. It also includes
reverse importers for common hand-written artifacts and a reproducible benchmark
that exercises compilation, round-trip import, and offline assertions without
calling external model APIs.

The software is packaged as a Python 3.11+ project with a Typer-based CLI, Pydantic
models, generated JSON Schema, pytest coverage for parser and compiler behavior, and
offline benchmark scripts. This keeps the core workflow inspectable: users can
validate a contract, inspect the normalized representation, compile target
artifacts, import an existing artifact, and test an output with deterministic local
commands.

# Statement of need

AI-assisted software workflows increasingly depend on repository-local instruction
files, editor-specific rules, structured output schemas, and tool-connection
protocols. These artifacts are useful, but they are usually maintained separately.
The same governance intent, for example "do not use the network", "ask before
writing files", "do not expose confidential inputs", or "return JSON matching this
schema", may need to be copied into several formats. This creates drift: one tool may
receive an updated rule while another keeps a stale version.

GovernSpec addresses this artifact-level problem for software teams, AI application
builders, governance reviewers, and researchers studying agent workflows. It gives
them a single structured source of truth that can be reviewed in version control and
compiled into downstream artifacts. It does not replace an agent runtime and it does
not claim runtime enforcement. Instead, it helps teams author, propagate, migrate,
and test the task contract around an agent run.

This distinction is important for research and practice. Many teams want governance
requirements to be visible before a model is invoked, but they also need to keep
using existing editors, model APIs, and agent tools. GovernSpec therefore focuses on
artifact compatibility and reproducible local checks rather than on runtime
interception. The resulting workflow is useful when a project needs lightweight
governance evidence without adopting a new orchestration framework.

# State of the field

Several ecosystems already define useful pieces of this workflow. Claude Code
documents project memory through `CLAUDE.md` files [@anthropic_memory]. Cursor
supports project rules stored as `.mdc` files [@cursor_rules]. OpenAI Structured
Outputs use JSON Schema to constrain model responses [@openai_structured_outputs],
and the Model Context Protocol defines a way for applications to expose tools and
context to models [@mcp_spec]. JSON itself and JSON Schema provide widely adopted
data-description foundations [@rfc8259; @json_schema_2020_12].

GovernSpec is also distinct from lightweight CI validators such as
`JanneL/validate-intentspec-action`, which validates Markdown front matter against a
small schema in GitHub Actions [@validate_intentspec_action]. GovernSpec instead
uses YAML contracts, reusable governance packs, a normalized intermediate
representation, target compilers, reverse importers, and offline output assertions.
Rather than introducing a new runtime or replacing editor-native artifacts, it
compiles a higher-level contract into the formats that existing tools already
understand. This design is also related to software-engineering evaluations of code
models and agent behavior, where explicit specifications and reproducible checks
are important for assessing generated outputs [@chen_codex; @jimenez_swebench].

# Research applications

GovernSpec can be used in research on AI coding tools, prompt and instruction
engineering, structured-output workflows, and software governance. The included
benchmark provides a small but reproducible artifact-level test bed: 20 contracts,
52 output samples, 20 hand-written artifacts, 6 compilation targets, and 10
deterministic assertion types. It is designed to run locally and to avoid real
external agent calls, making it suitable for repeatable tool experiments and for
teaching artifact-level governance concepts.

For practitioners, GovernSpec supports incremental adoption. A team can start from
an existing instruction file, import it into a draft contract, edit the structured
contract, compile it to multiple target artifacts, and check outputs in CI. This
workflow makes governance requirements visible as code-reviewable project assets
rather than scattered prompt text.

For tool researchers, the intermediate representation and benchmark results provide
observable failure modes. A target may be unable to preserve a human confirmation
gate, or a structured-output artifact may preserve a JSON schema while losing
natural-language constraints. GovernSpec records these differences as capability
notes and field-level fidelity results, which makes the limits of artifact
translation explicit instead of treating every compiled output as semantically
equivalent.

# AI usage disclosure

OpenAI Codex was used to assist with software implementation, documentation,
benchmark construction, and paper drafting. The author reviewed, edited, and is
responsible for all submitted code, data, documentation, and manuscript text.

# References
