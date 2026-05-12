# `*.govern.yaml` Tutorial

This guide is for first-time GovernSpec users. By the end, you should be able to create a valid `*.govern.yaml` file, inspect it, compile it into downstream artifacts, and test an agent output against it.

GovernSpec has a small mental model:

```text
*.govern.yaml       = an AI task contract
governspec validate = check whether the contract is valid
governspec inspect  = show the normalized rules
governspec compile  = turn the contract into a target artifact
governspec test     = check an output against the contract
```

GovernSpec does not call a real LLM API and does not require an API key. It manages task rules and generated artifacts. It does not replace an agent runtime or a permission sandbox.

## 1. When to Use `*.govern.yaml`

Use a `*.govern.yaml` file when an AI task needs clear boundaries:

- Code review: read the repository, but do not edit files.
- Customer brief: use provided materials, but do not expose private data.
- Contract review: flag risks and uncertainty, but do not provide final legal advice.
- Quality review: always include the same sections and risk categories.
- JSON report: produce output that matches a JSON schema.

For a one-off question, a prompt is usually enough. Use GovernSpec when the task should be reused, reviewed in Git, compiled to multiple tools, or checked in CI.

## 2. Start With a Draft

You do not need to write YAML from scratch. Start with a natural-language draft:

```bash
governspec draft "Review this repository without editing files or using network access. Return an overall assessment, must-fix issues, suggestions, and test advice." --out examples/my_review.govern.yaml
```

Then validate it:

```bash
governspec validate examples/my_review.govern.yaml
```

Inspect the normalized result:

```bash
governspec inspect examples/my_review.govern.yaml
```

`draft` is local and heuristic. It is useful for getting started, but you should still review permissions, constraints, output sections, and tests before using the contract.

## 3. Start From a Template

You can also create a blank template:

```bash
governspec init --file examples/my_task.govern.yaml
```

For a Chinese placeholder template:

```bash
governspec init --file examples/my_task.govern.yaml --locale zh-CN
```

After creating the file, edit these fields first:

- `metadata.name`
- `task.goal`
- `inputs`
- `permissions`
- `constraints`
- `output`
- `tests`

## 4. Complete Example

This contract describes a read-only repository review. You can copy it and adjust it for your own task.

```yaml
version: "0.1"
kind: "GovernSpec"

metadata:
  name: "code_review"
  title: "Repository code review"
  description: "Review repository changes without directly editing code."
  owner: "engineering"

task:
  goal: "Review the codebase and summarize defects, risks, and follow-up tests."
  audience:
    - "Software engineer"
    - "Tech lead"
  priority: "medium"

context:
  domain: "Software engineering"
  facts: []
  assumptions:
    - "When repository context is incomplete, state the assumption explicitly."
  glossary: {}

inputs:
  - name: "repository"
    type: "directory"
    path: "."
    required: true
    privacy: "internal"

permissions:
  web: false
  filesystem:
    read: true
    write: false
  network: false
  tools:
    send_email: false
    read_calendar: false
    read_gmail: false
    create_file: false
    delete_file: false
    purchase: false

constraints:
  - "Do not directly modify code."
  - "Do not delete files."
  - "State assumptions when evidence is incomplete."

evidence:
  require_sources: false
  mark_uncertainty: true
  distinguish:
    - "issue"
    - "suggestion"

output:
  format: "markdown"
  language: "en"
  max_words: 900
  sections:
    - "Overall Assessment"
    - "Must Fix"
    - "Suggestions"
    - "Test Advice"

quality:
  tone:
    - "clear"
    - "direct"
  must_include: []
  must_avoid:
    - "rewriting the repository"

human_gates: []

tests:
  - name: "All sections must be present"
    assert:
      - type: "required_sections"
  - name: "Must not claim code was modified"
    assert:
      - type: "not_contains"
        value: "I have changed the code"
```

## 5. What Each Field Does

| Field | Purpose | Common Use |
| --- | --- | --- |
| `version` | GovernSpec schema version | Use `"0.1"` |
| `kind` | Document type | Use `"GovernSpec"` for one task |
| `metadata` | Name, title, description, owner | Helps people identify the contract |
| `task` | Goal, audience, priority | Defines what the agent should do |
| `context` | Domain, facts, assumptions, glossary | Records background and uncertainty |
| `inputs` | Materials the task may use | Files, directories, documents, JSON |
| `permissions` | Allowed and forbidden capabilities | Web, network, filesystem, tools |
| `constraints` | Hard rules | Things the agent must or must not do |
| `evidence` | Evidence policy | Source requirements and uncertainty handling |
| `output` | Output shape | `markdown`, `text`, or `json` |
| `quality` | Style and content preferences | Tone, required text, forbidden text |
| `human_gates` | Confirmation rules | When to ask a human before continuing |
| `tests` | Offline checks | Sections, length, text rules, JSON schema |

The five fields you should understand first are:

```text
task        = what the agent should do
permissions = what the agent may or may not do
constraints = rules the agent must follow
output      = what the final answer should look like
tests       = how to check the final answer
```

## 6. Compile to `AGENTS.md`

After validation passes, compile the contract into an `AGENTS.md` style file:

```bash
governspec compile examples/my_review.govern.yaml --target agents-md --out examples/my_review.agents.md
```

Without `--out`, the compiled artifact is printed to the terminal:

```bash
governspec compile examples/my_review.govern.yaml --target agents-md
```

Common targets:

| Target | Output |
| --- | --- |
| `agents-md` | `AGENTS.md` style instructions |
| `prompt` | Generic Markdown prompt |
| `openai-structured` | OpenAI Structured Outputs payload |
| `gemini-structured` | Gemini structured output payload |
| `mcp-plan` | MCP execution plan summary |
| `skill` | Generic skill bundle |

## 7. Test an Output

Suppose the agent output is saved as `output.md`:

```bash
governspec test examples/my_review.govern.yaml --output output.md
```

The command checks the assertions in `tests`. Common assertions include:

- `required_sections`: output must contain all `output.sections`.
- `not_contains`: output must not contain a specific string.
- `contains`: output must contain a specific string.
- `max_words`: output must stay within `output.max_words`.
- `json_schema`: JSON output must match the schema.

These checks are deterministic. They can verify shape, length, required text, forbidden text, and JSON structure. They do not prove that every factual claim is correct.

## 8. JSON Output

Markdown output uses `sections`. JSON output uses `schema`:

```yaml
output:
  format: "json"
  language: "en"
  schema:
    type: "object"
    additionalProperties: false
    required:
      - "summary"
      - "risks"
    properties:
      summary:
        type: "string"
      risks:
        type: "array"
        items:
          type: "string"

tests:
  - name: "Output must match JSON schema"
    assert:
      - type: "json_schema"
  - name: "Risks field must exist"
    assert:
      - type: "json_path_exists"
        path: "$.risks"
```

Compile it for OpenAI Structured Outputs:

```bash
governspec compile report.govern.yaml --target openai-structured --out report.openai-structured.json
```

## 9. Adapting the Template to Your Domain

The structure is generic. The content must match your domain.

| Domain | Fields to Review Closely |
| --- | --- |
| Software engineering | `inputs`, `permissions.filesystem`, `constraints`, test sections |
| Manufacturing | `context.domain`, quality standards, severity levels, human gates |
| Legal | disclaimers, evidence policy, limits on legal advice |
| Finance | data sources, risk warnings, limits on investment advice |
| Healthcare | privacy rules, non-diagnostic language, human confirmation rules |
| Sales | customer data privacy, output structure, follow-up boundaries |

GovernSpec does not know your industry rules by itself. Put the rules that matter into `constraints`, `evidence`, and `human_gates`.

## 10. Pre-Commit Checklist

Before committing a `*.govern.yaml` file:

- Run `governspec validate <file>`.
- Run `governspec inspect <file>` and check the final permissions and constraints.
- Make sure `permissions` does not accidentally allow network, writes, deletion, purchases, or other high-risk actions.
- Keep `constraints` specific.
- Use `output.sections` for sections that readers actually need.
- Add at least one meaningful `tests` assertion.
- Add `human_gates` for high-risk actions.
- Treat compiled files as generated artifacts. Change the contract first, then compile again.

## 11. Common Mistakes

### Misspelled Fields

GovernSpec rejects unknown fields. For example, use `output`, not `outputs`.

### Missing `max_words`

`markdown` and `text` outputs require `max_words`. If you do not want a tight limit, use a larger value.

### Wrong JSON Schema Key

In YAML, use `schema`:

```yaml
output:
  format: "json"
  schema:
    type: "object"
```

Do not use `json_schema` in the YAML file.

### Goal Without Permissions

`task.goal` says what the task is. `permissions` says what the task may do. You need both.

### Treating Tests as Fact Checks

`governspec test` can check structure and explicit rules. It cannot prove that complex factual claims are true.

## 12. Recommended Workflow

For most tasks:

```bash
governspec draft "Describe your task in plain language" --out task.govern.yaml
governspec validate task.govern.yaml
governspec inspect task.govern.yaml
governspec compile task.govern.yaml --target agents-md --out task.agents.md
governspec test task.govern.yaml --output output.md
```

If you prefer a blank template:

```bash
governspec init --file task.govern.yaml
```

If you already have `AGENTS.md`:

```bash
governspec import AGENTS.md --out imported.govern.yaml
governspec validate imported.govern.yaml
governspec inspect imported.govern.yaml
```

The safest habit is to maintain `*.govern.yaml` as the source of truth, then compile downstream files from it. That keeps rules reviewable and reduces drift between tools.
