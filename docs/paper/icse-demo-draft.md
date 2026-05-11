# GovernSpec: Zero-Intrusion Contract Compilation and Offline Acceptance Testing for Heterogeneous AI Agents

Ting Liu  
SymbolicLight Research  
Foshan, Guangdong, China  
research@symboliclight.com

## Abstract

AI-assisted software teams increasingly rely on heterogeneous agent interfaces:
repository instruction files, IDE rule files, structured-output schemas, and
machine-readable planning artifacts. The governance intent behind these artifacts is
often stable across tools, but the artifacts themselves are duplicated, edited, and
reviewed in incompatible formats. This fragmentation makes it difficult to keep
permissions, safety constraints, human confirmation rules, and output requirements
consistent without modifying every downstream agent runtime.

We present GovernSpec, a local-first tool that turns a single task-governance
contract into native artifacts for multiple AI-agent workflows. Developers author an
`govern.yaml` contract describing the task goal, permissions, constraints,
confirmation gates, output contract, and deterministic acceptance tests. GovernSpec
validates the contract, resolves reusable governance packs, normalizes it into an
intermediate intent representation, compiles target-specific artifacts, supports
reverse import from existing artifacts, and checks generated outputs with offline
assertions. The prototype currently implements 10 compile targets, 5 import source
types, and 10 deterministic assertion types. In a repository-local benchmark with
20 contracts, 52 output samples, and 20 handwritten artifacts, 94 of 120
representative contract-target pairs compiled successfully (78.33%); compiled
round-trip import succeeded for 74 of 100 attempted artifacts (74.0%); handwritten
artifact import succeeded for 20 of 20 artifacts; all 20 valid outputs passed
offline checks; and the targeted defect suite caught 32 of 32 labeled defects.
These results demonstrate the
feasibility of a zero-intrusion, artifact-level governance workflow for settings in
which teams cannot or do not want to modify agent runtimes.

## 1. Introduction

Modern software teams rarely use a single AI-assistance surface. A repository may
contain durable project instructions, an IDE may consume project-scoped rule files,
an API integration may require a JSON schema, and an MCP-based workflow may exchange
machine-readable plans. These channels are useful because they meet developers where
they already work. They also create a governance maintenance problem: the same
requirements must be translated into several formats, each with different expressive
power and review affordances.

Consider a team that wants an agent to review a release plan. The policy is simple:
do not read private customer data, do not access the network, ask before destructive
file operations, produce a bounded report with required sections, and fail the output
if it contains unsupported claims. In practice, that policy may be copied into
markdown instructions, Cursor rule files, structured-output payloads, and MCP plans.
Each copy can drift. Some formats can express natural-language instructions but not a
schema. Some can express a JSON schema but not human confirmation gates. A reviewer
must understand every target format before judging whether the policy still matches
the original intent.

GovernSpec addresses this artifact-level problem. It is not an agent runtime, a
monitor, or a fail-closed policy enforcement layer. Instead, it provides a small
compiler and validator for task-governance contracts. A developer writes one
`govern.yaml` file. GovernSpec compiles that contract into the native artifact
channels used by downstream tools and then provides deterministic offline checks for
the final output.

This demonstration answers the following question: can a single local contract be
compiled into heterogeneous AI-agent artifacts, imported back into a structured
representation, and used to validate outputs without calling an external LLM service
or modifying an agent runtime?

The paper makes four concrete contributions:

1. A local-first contract workflow for making task goals, permissions, constraints,
   human gates, output requirements, and acceptance tests reviewable in one source.
2. A target compiler that lowers the same contract into multiple agent-native
   artifacts, including instruction markdown, IDE rules, structured-output schemas,
   and MCP-style plans.
3. A reverse-import workflow for migrating generated or handwritten artifacts back
   into draft contracts, exposing fidelity loss rather than hiding it.
4. A reproducible artifact-level benchmark and offline assertion suite that evaluate
   compilation coverage, round-trip fidelity, and deterministic defect detection.

## 2. Background and Positioning

GovernSpec is motivated by a growing set of tool-specific artifact channels. Claude
Code documents project memory through `CLAUDE.md` files [1]. Cursor project rules
are stored as `.mdc` files with metadata and markdown content [2]. OpenAI Structured
Outputs accept JSON Schema-based response formats for schema-constrained model
outputs [3]. The Model Context Protocol defines a machine-readable protocol for
connecting model applications with tools and context sources [4].

This tool context sits within a broader software-engineering literature on LLM
coding assistance, agentic tool use, and prompt engineering. Code-generation
benchmarks and real-repository tasks show that LLMs can assist software work but
also require external validation [5-7]. Studies of coding assistants report
productivity benefits as well as security and over-trust risks [8,9].
Prompt-pattern and agent research further suggests that reusable instructions and
tool context are central to reliable human-agent workflows [10,11].

These systems are not interchangeable. They expose different integration points,
different artifact formats, and different guarantees. GovernSpec therefore does not
attempt to define a new universal agent runtime. Its narrower contribution is a
compilation layer above existing artifact channels. The source contract captures the
governance intent once; target backends translate what each downstream channel can
represent; and capability notes make target limitations explicit.

This positioning also shapes the validation claim. Native instruction files and IDE
rules are advisory artifacts, not runtime monitors. GovernSpec therefore avoids
claiming that it can prevent unsafe actions at execution time. It demonstrates that a
team can author, propagate, migrate, and test governance intent locally, with
deterministic artifacts that are suitable for review and continuous integration.

GovernSpec is also distinct from lightweight CI validators such as
`validate-intentspec-action`. That action checks Markdown front matter against a
small schema in GitHub Actions. GovernSpec uses YAML contracts, reusable governance
packs, a normalized intermediate representation, target-specific compilers, reverse
importers, and offline output assertions. The comparison is useful because both
projects care about explicit AI task artifacts, but they occupy different layers of
the workflow.

## 3. Tool Design

GovernSpec has five internal stages:

```text
govern.yaml
  -> parse and validate
  -> resolve imported governance packs
  -> normalize to the intermediate intent representation
  -> compile to target-specific artifacts
  -> test generated outputs offline
```

The source contract is a YAML document containing metadata, task context, inputs,
permissions, constraints, evidence expectations, output requirements, human
confirmation gates, and tests. Reusable policy fragments are represented as
`GovernPack` files. Import resolution applies conservative merge behavior, including
deny-wins permissions and preservation of imported acceptance assertions.

The intermediate intent representation (IIR) separates authoring concerns from
target formatting. It stores the normalized task goal, resolved permissions, merged
constraints, output contract, human gates, test contracts, risk signals, and target
capability notes. Backends then lower the IIR into concrete target families. For
instruction-style targets, GovernSpec emits markdown. For Cursor rules, it emits a
rule bundle. For structured-output targets, it emits JSON schema payloads. For MCP
planning, it emits a machine-readable plan with risk and constraint-loss fields.

The offline acceptance runner evaluates final artifacts after an agent has produced
an output. It supports required sections, required and forbidden substrings, regular
expression checks, word and character limits, JSON schema validation, JSON path
existence, and JSON array size constraints. These checks deliberately focus on
deterministic compliance properties. They do not verify semantic truth, factual
correctness, or whether a model internally followed the instructions.

## 4. Demonstration Scenario

The demonstration uses the repository-local benchmark in
`benchmark/paper_icse2027/`. It contains 20 contracts, 52 output samples, 20
handwritten artifacts, explicit labels, experiment scripts, and generated results.
The benchmark is designed to run without external model APIs or network-dependent
agent services.

The live demonstration has four segments. First, the presenter authors or edits a
small `govern.yaml` contract with a task goal, permissions, human gates, output
requirements, and tests. Second, GovernSpec compiles the same contract into
representative targets: `agents-md`, `claude-md`, `cursor-rules`,
`openai-structured`, `gemini-structured`, and `mcp-plan`. Third, the presenter
reverse-imports generated and handwritten artifacts into draft contracts and shows
where fidelity is preserved or lost. Fourth, the presenter runs the offline
acceptance runner against valid and defective outputs, showing deterministic failure
messages for missing sections, forbidden text, malformed JSON, and schema mismatch.

All experiments are reproducible with a single command from the repository root:

```bash
python benchmark/paper_icse2027/scripts/run_all.py
```

The command generates `compile_matrix.json`, `roundtrip_fidelity.json`,
`assertion_eval.json`, `summary.json`, `tables.md`, and `numbers.md` under
`benchmark/paper_icse2027/results/`.

## 5. Initial Validation

The validation is intentionally artifact-level. It evaluates whether the current
implementation can compile representative contracts, recover structured drafts from
artifacts, and detect labeled output defects. It does not evaluate live agent
behavior.

### 5.1 Multi-Target Compilation

The compile matrix evaluates 20 contracts against 6 representative targets, producing
120 contract-target pairs. Table 1 reports target-level coverage. Instruction-style
targets and `mcp-plan` compiled for all contracts. Structured-output targets
compiled for JSON-output contracts and failed for markdown-output contracts. These
failures are expected target limitations because schema-constrained output targets
require JSON output contracts.

**Table 1. Target coverage in the compile matrix.**

| Target | Succeeded | Total |
| --- | ---: | ---: |
| `agents-md` | 20 | 20 |
| `claude-md` | 20 | 20 |
| `cursor-rules` | 20 | 20 |
| `openai-structured` | 7 | 20 |
| `gemini-structured` | 7 | 20 |
| `mcp-plan` | 20 | 20 |

Overall, 94 of 120 contract-target pairs compiled successfully (78.33%).

### 5.2 Reverse Import Fidelity

The round-trip experiment compiles contracts into the 5 importable source types and
imports them back into draft contracts. The comparison focuses on core fields:
`goal`, `permissions`, `constraints`, `human_gates`, `output`, and `tests`.
Non-core metadata and source-path fields are ignored. JSON schemas are normalized
with stable key ordering before comparison.

**Table 2. Round-trip import and core-field fidelity.**

| Source type | Imported | Average field fidelity |
| --- | ---: | ---: |
| `agents-md` | 20 | 77.5% |
| `claude-md` | 20 | 77.5% |
| `cursor-rules` | 20 | 77.5% |
| `gemini-structured` | 7 | 47.62% |
| `openai-structured` | 7 | 47.62% |

Compiled round-trip import succeeded for 74 of 100 attempted artifacts (74.0%).
Successful compiled round trips had an average core-field fidelity of 71.85%. The
benchmark also imports 20 handwritten artifacts and matches them against partial gold
labels; all 20 imported successfully. These results show that generated instruction
artifacts preserve more recoverable governance information than structured-output
payloads, while structured-output payloads remain useful for output schema recovery.

### 5.3 Offline Assertion Effectiveness

The assertion experiment evaluates 20 valid outputs and 32 targeted defect outputs.
The defect suite contains at least two samples for each supported assertion type.

**Table 3. Targeted defect detection by assertion type.**

| Assertion | Targeted samples | Caught | Catch rate |
| --- | ---: | ---: | ---: |
| `contains` | 6 | 6 | 100.0% |
| `json_array_min_items` | 2 | 2 | 100.0% |
| `json_path_exists` | 2 | 2 | 100.0% |
| `json_schema` | 2 | 2 | 100.0% |
| `max_chars` | 2 | 2 | 100.0% |
| `max_words` | 3 | 3 | 100.0% |
| `no_regex` | 4 | 4 | 100.0% |
| `not_contains` | 4 | 4 | 100.0% |
| `regex` | 3 | 3 | 100.0% |
| `required_sections` | 4 | 4 | 100.0% |

All 20 valid outputs passed offline acceptance tests (100.0%), and the targeted
defect suite caught 32 of 32 labeled defects (100.0%). The observed failures cover
missing markdown sections, forbidden content, absent required content, regex
mismatch, forbidden regex matches, length violations, JSON schema mismatch, missing
JSON paths, and undersized JSON arrays.

## 6. Threats to Validity and Limitations

The benchmark is small and curated. It is appropriate for demonstrating feasibility,
but it is not evidence of broad empirical generality across all agent tools,
repositories, or policy styles. The contracts intentionally cover markdown and JSON
outputs, English and Chinese text, imports, human gates, filesystem and network
risks, and all supported assertion types, but the suite remains a seed benchmark.

The validation isolates artifact behavior from model behavior. This design makes the
experiments deterministic and reproducible, but it also means the results do not
measure whether a live agent follows a compiled instruction file in practice.
GovernSpec should therefore be viewed as an authoring, propagation, migration, and
post-hoc validation layer rather than as runtime security enforcement.

Reverse import is heuristic for natural-language artifacts. It can recover goals,
constraints, permissions, and output hints from generated or handwritten artifacts,
but it cannot guarantee semantic equivalence with the original author intent. The
tool exposes this limitation through field-level fidelity rather than hiding it
behind a binary success metric.

## 7. Availability

GovernSpec is implemented as a Python 3.11+ local CLI and library. The benchmark and
generated results are included under `benchmark/paper_icse2027/`. The prototype does
not call real LLM APIs, does not require API keys, and does not require network
access for the reported experiments. The local reproduction command is:

```bash
python benchmark/paper_icse2027/scripts/run_all.py
```

## References

[1] Anthropic. "How Claude remembers your project." Claude Code Docs. Accessed Apr.
24, 2026. https://code.claude.com/docs/en/memory

[2] Cursor. "Rules." Cursor Documentation. Accessed Apr. 24, 2026.
https://docs.cursor.com/context/rules

[3] OpenAI. "Structured model outputs." OpenAI API Documentation. Accessed Apr. 24,
2026. https://developers.openai.com/api/docs/guides/structured-outputs

[4] Model Context Protocol. "Specification." Model Context Protocol Documentation.
Accessed Apr. 24, 2026. https://modelcontextprotocol.io/specification/draft

[5] Chen et al. "Evaluating Large Language Models Trained on Code." arXiv, 2021.
https://arxiv.org/abs/2107.03374

[6] Jimenez et al. "SWE-bench: Can Language Models Resolve Real-World GitHub
Issues?" ICLR, 2024. https://openreview.net/forum?id=VTF8yNQM66

[7] Fan et al. "Large Language Models for Software Engineering: Survey and Open
Problems." arXiv, 2023. https://arxiv.org/abs/2310.03533

[8] Peng et al. "The Impact of AI on Developer Productivity: Evidence from GitHub
Copilot." arXiv, 2023. https://arxiv.org/abs/2302.06590

[9] Perry et al. "Do Users Write More Insecure Code with AI Assistants?" CCS, 2023.
https://doi.org/10.1145/3576915.3623157

[10] White et al. "A Prompt Pattern Catalog to Enhance Prompt Engineering with
ChatGPT." arXiv, 2023. https://arxiv.org/abs/2302.11382

[11] Yao et al. "ReAct: Synergizing Reasoning and Acting in Language Models." ICLR,
2023. https://openreview.net/forum?id=WE_vluYUL-X
