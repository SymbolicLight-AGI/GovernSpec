# IntentSpec: Zero-Intrusion Contract Compilation and Offline Acceptance Testing for Heterogeneous AI Agents

## Abstract

AI agent teams increasingly depend on heterogeneous tools such as repository
instruction files, IDE rules, structured-output payloads, and MCP plans. Governance
requirements are often duplicated across these artifacts as free text, making them
hard to review, propagate, and validate consistently. Existing runtime-centered
approaches can provide stronger action-time control, but they require integration
points that are unavailable or undesirable in many off-the-shelf agent toolchains.

We present IntentSpec, a local-first tool for authoring a single governance contract
and compiling it into native artifacts consumed by heterogeneous AI agent workflows.
IntentSpec validates a YAML source contract, resolves reusable governance packs,
normalizes the task into an intermediate representation, compiles target-specific
artifacts, and validates generated outputs with deterministic offline assertions.
The current prototype implements 10 compile targets, 5 import source types, and 10
deterministic assertion types. In a local artifact-level benchmark, the compile
matrix contains 48 contract-target pairs across 8 contracts and 6 representative
targets; 38 compiled successfully (79.17%). Compiled round-trip import succeeded for
30 of 40 attempted artifacts (75.0%), with 70.55% average core-field fidelity among
successful compiled round trips. All 8 valid outputs passed offline checks, and the
targeted defect suite caught 10 of 10 labeled defects. These results show the
feasibility of a zero-intrusion governance layer for settings where modifying agent
runtimes is not practical.

## Introduction

Modern AI-assisted software work rarely happens in a single agent runtime. A team may
use Codex-style repository instructions, Claude Code project files, Cursor rules, and
API-level structured output in the same repository. The governance requirements are
often stable across these tools: do not expose private data, do not delete files,
ask for confirmation before high-risk actions, produce a report with required
sections, and keep the result within a size limit. The artifacts that carry these
requirements, however, are not stable or uniform. They are markdown files, IDE rule
documents, JSON schema payloads, and machine-readable plans.

This fragmentation creates an ordinary but costly software engineering problem.
Teams must duplicate the same governance policy across multiple artifacts, review
changes in several formats, and hope that the resulting instructions remain
consistent. Runtime-centered policy systems address a related problem by intercepting
actions, monitoring tool calls, or evaluating policies during execution. Those
approaches are valuable when the team controls the agent runtime. They are less
usable when the toolchain exposes only native instruction artifacts or structured
output configuration.

IntentSpec addresses the artifact-level side of this problem. Developers write a
single `intent.yaml` contract that describes the task goal, permissions, constraints,
human confirmation gates, output contract, and deterministic acceptance tests. The
tool compiles this contract into native downstream artifacts, including `AGENTS.md`,
`CLAUDE.md`, Cursor rules, OpenAI Structured Outputs payloads, Gemini structured
output payloads, and MCP plans. It also supports reverse import from existing
artifacts into draft contracts, making migration from handwritten instructions
possible.

The core research question for this demonstration is: can a single contract be
compiled into native governance artifacts across heterogeneous AI agent toolchains,
without modifying their runtimes, while still supporting deterministic post-hoc
validation of generated outputs?

This paper contributes:

1. A local-first tool workflow for authoring a single governance contract and
   compiling it into multiple agent-native artifacts.
2. An intermediate representation that separates the authoring schema from
   target-specific artifact generation.
3. A reverse-import workflow for reconstructing structured contracts from compiled
   or handwritten artifacts.
4. A deterministic offline acceptance test runner that checks generated outputs
   without calling an LLM.

## Tool Overview

IntentSpec is intentionally small. It is not an agent runtime, and it does not call
LLM APIs. Its job is to make governance intent explicit, portable, and testable.

The workflow has six steps:

```text
intent.yaml
  -> validate
  -> resolve imports
  -> normalize to IIR
  -> compile to target artifact
  -> run agent in the target toolchain
  -> test the output offline
```

The source contract is a YAML document. It contains metadata, a task goal,
permissions, constraints, evidence rules, output expectations, human gates, and
tests. Reusable policy fragments can be stored as `IntentPack` files and imported
into contracts. Import resolution applies conservative merge behavior such as
deny-wins permissions and preserving imported acceptance assertions.

After parsing and import resolution, IntentSpec builds an intermediate intent
representation (IIR). The IIR stores normalized goal text, resolved permissions,
merged constraints, output contracts, human gates, test contracts, risk signals, and
target capability notes. The compiler lowers this IIR into each target family. For
instruction targets, it emits markdown documents. For structured-output targets, it
emits JSON schema payloads. For MCP planning, it emits a machine-readable plan with
risk level and constraint-loss notes.

The acceptance runner evaluates final outputs using deterministic checks. The current
prototype supports required sections, containment and forbidden containment, regular
expression checks, word and character limits, JSON schema validation, JSON path
existence, and JSON array size checks. These assertions do not judge semantic truth.
They are designed to catch reproducible compliance failures such as missing sections,
forbidden text, malformed JSON, and output contract violations.

## Key Design Choices

First, IntentSpec uses existing artifact channels instead of requiring runtime
modification. This is the main reason the tool can support heterogeneous workflows.
If a platform already reads `AGENTS.md`, `CLAUDE.md`, `.mdc` rules, or structured
output JSON, IntentSpec compiles into that channel.

Second, the IIR keeps authoring concerns separate from target-specific formatting.
The YAML schema is designed for humans to write and review. The target artifacts are
designed for specific tools to consume. The IIR is the boundary between those two
worlds, which keeps target backends small and makes reverse import easier to reason
about.

Third, IntentSpec treats target limitations as part of the user experience. Some
targets can express natural-language constraints but cannot enforce JSON schema.
Other targets can enforce JSON structure but cannot represent human confirmation
rules. The `mcp-plan` target exposes this mismatch through `constraint_loss`; the
paper benchmark treats this as an example of compile-time loss reporting rather than
a universal loss API across all targets.

Fourth, offline acceptance testing complements zero-intrusion compilation. Native
instruction artifacts are advisory channels, so IntentSpec does not claim fail-closed
runtime enforcement. Instead, it gives teams a reproducible way to detect whether an
agent output violates the contract after generation.

## Demonstration Scenario and Initial Validation

The demonstration uses a repository-local benchmark under
`benchmark/paper_icse2027/`. It includes 8 contracts, 18 output samples, 6
handwritten artifacts, and scripts for compilation, round-trip import, assertion
evaluation, and table rendering. The benchmark does not call external agent services.
This keeps the demonstration reproducible on a developer machine and avoids mixing
tool behavior with model behavior.

The multi-target compilation experiment evaluates 8 contracts against 6
representative targets: `agents-md`, `claude-md`, `cursor-rules`,
`openai-structured`, `gemini-structured`, and `mcp-plan`. The compile matrix contains
48 contract-target pairs; 38 compiled successfully (79.17%). All instruction-style
and MCP-plan targets compiled for all contracts. Structured-output targets compiled
for the JSON-output contracts and failed for markdown-output contracts, which is an
expected target limitation rather than a runtime error.

The round-trip experiment compiles contracts into the 5 importable source types and
imports them back into draft contracts. Compiled round-trip import succeeded for 30
of 40 attempted artifacts (75.0%). Successful compiled round trips had an average
core-field fidelity of 70.55%. The benchmark also imports 6 handwritten artifacts and
matches them against partial gold labels; all 6 imported successfully. These results
illustrate that IntentSpec can support both precise migration from generated
artifacts and heuristic recovery from human-written artifacts, while making fidelity
loss visible.

The assertion experiment evaluates 8 valid outputs and 10 targeted defect outputs.
All 8 valid outputs passed offline acceptance tests (100.0%). The targeted defect
suite caught 10 of 10 labeled defects (100.0%), with one sample for each supported
assertion type. The defects cover missing markdown sections, forbidden text, required
text absence, regex mismatch, regex-forbidden content, word-limit violations,
character-limit violations, JSON schema mismatch, missing JSON paths, and undersized
JSON arrays.

These results are intentionally scoped. They do not show that IntentSpec can prevent
an agent from taking an unsafe action at runtime. They show that a single source
contract can be compiled across heterogeneous artifact formats, imported back into a
structured representation, and used to evaluate outputs without external services.

## Availability

The benchmark can be reproduced locally from the repository root:

```bash
python benchmark/paper_icse2027/scripts/run_all.py
```

The command writes JSON results and paper-friendly Markdown tables to
`benchmark/paper_icse2027/results/`. The generated files include:

- `compile_matrix.json`
- `roundtrip_fidelity.json`
- `assertion_eval.json`
- `summary.json`
- `tables.md`
- `numbers.md`

The demo video should show the same workflow in four short segments: author a
contract, compile to multiple targets, reverse-import an artifact, and run offline
acceptance tests against valid and defective outputs.
