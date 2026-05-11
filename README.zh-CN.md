# GovernSpec

[English README](README.md)

GovernSpec 是本仓库实现的一个**离线契约编译器**，用来统一管理 AI agent 的任务规则。

它让你维护一份 `govern.yaml`，然后编译成不同工具能直接读取的 artifact，例如
`AGENTS.md`、`CLAUDE.md`、Cursor Rules、OpenAI Structured Outputs、Gemini
structured output payload 和 MCP plan。

```text
govern.yaml
  -> validate
  -> resolve imports
  -> inspect normalized IIR
  -> compile to target artifacts
  -> run your agent
  -> test the output offline
```

> Define once, validate and compile everywhere.

GovernSpec 不调用真实 LLM，不需要 API key，不接管 agent runtime。它只做三件事：

- 把任务目标、权限、约束、人工确认门、输出格式和验收测试写成结构化 contract。
- 把 contract 编译成各个 AI 工具需要的格式。
- 对 agent 最终输出做 deterministic offline acceptance tests。

如果你第一次接触这个项目，建议先读本文，再读 [docs/technical-guide.md](docs/technical-guide.md)。

## 命名与第三方项目说明

本项目不隶属于、也不代表 `intentspec.org`、`JanneL/validate-intentspec-action` 或任何同名第三方项目。公开引用时，建议使用 **GovernSpec** 或 **GovernSpec v0.1 YAML contract toolchain** 来指代本仓库，避免和只校验 Markdown front matter 的 GitHub Action 混淆。

当前实现使用 `govern.yaml`、`GovernSpec` / `GovernPack`、Pydantic v2 schema、IIR、target compiler、reverse importer 和 offline assertion runner。它不是某个外部 GovernSpec 标准的官方实现，也不会声明自己是生态中的唯一或官方标准。

## 适合谁

### 使用多个 AI coding 工具的工程团队

如果你同时使用 Cursor、Codex、Claude Code 或 API structured outputs，就会遇到同一套规则重复维护的问题。GovernSpec 可以把这些规则收敛到一份 `govern.yaml`，再编译到不同工具。

### AI 应用开发者

如果你的应用需要稳定输出 JSON、限制模型行为、要求人工确认或在 CI 中检查输出格式，GovernSpec 可以提供本地 schema、编译和测试流程。

### 安全、治理和合规负责人

如果你关心 agent 能不能联网、能不能写文件、是否暴露隐私、是否需要人工确认，GovernSpec 把这些内容变成显式字段，而不是散落在 prompt 里。

### 研究者和工具作者

GovernSpec 提供 schema、IIR、importer、compiler、benchmark 和 offline assertion runner，适合研究 agent artifact-level governance、round-trip fidelity 和 task contract portability。

## 不适合谁

GovernSpec 不是：

- LLM runtime
- agent orchestration framework
- 权限沙箱
- runtime enforcement system
- MCP 替代品
- Cursor、Codex、Claude Code 的替代品

它能帮助你更清晰地表达、传播和检查规则，但不能保证模型在运行时一定不会违规。

## 你能得到什么

使用 GovernSpec 后，团队可以得到：

- 一份可 code review 的 AI 任务契约。
- 多个下游工具能读取的目标文件。
- 可复用的治理规则包 `GovernPack`。
- 明确的权限边界和人工确认规则。
- 可在本地或 CI 中运行的输出验收测试。
- 从已有 `AGENTS.md`、`CLAUDE.md`、Cursor Rules 或 structured output JSON 迁移回 contract 的路径。
- 对目标工具能力边界的可见性，例如哪些约束无法完整编译到某个 target。

## 安装

要求 Python 3.11+。

从 PyPI 安装：

```bash
pip install governspec
```

从源码安装：

```bash
git clone https://github.com/SymbolicLight-AGI/GovernSpec.git
cd GovernSpec
pip install -e ".[dev]"
```

检查安装：

```bash
governspec doctor
```

GovernSpec 的核心流程不需要 API key，不需要联网。

## 5 分钟快速开始

### 1. 创建 contract

```bash
governspec init
```

如果希望生成中文占位说明，可以使用：

```bash
governspec init --locale zh-CN
```

这会生成 `govern.yaml`。你可以先用下面这个最小示例理解结构：

```yaml
version: "0.1"
kind: "GovernSpec"

metadata:
  name: "code_review"
  title: "Code review report"
  owner: "dev-team"

task:
  goal: "Review the codebase and produce a report without modifying files."
  priority: "high"

permissions:
  web: false
  filesystem:
    read: true
    write: false
  network: false
  tools:
    delete_file: false
    purchase: false

constraints:
  - "Do not fabricate facts."
  - "Do not modify existing code."

human_gates:
  - when: "A destructive action is required"
    action: "ask_confirmation"

output:
  format: "markdown"
  language: "en"
  max_words: 800
  sections:
    - "Summary"
    - "Findings"
    - "Testing"

tests:
  - name: "Must include all sections"
    assert:
      - type: "required_sections"
  - name: "Must stay concise"
    assert:
      - type: "max_words"
```

### 2. 验证 contract

```bash
governspec validate govern.yaml
```

看到 `Validation status: ok` 表示 schema 和字段约束通过。

### 3. 查看最终归一化结果

```bash
governspec inspect govern.yaml
```

`inspect` 展示 import 解析、权限合并和 normalization 之后的 IIR。调试复杂 contract 时，这一步很有用。

如果要给脚本使用：

```bash
governspec inspect govern.yaml --format json
```

### 4. 编译到目标工具

编译给 Codex 或其他读取 `AGENTS.md` 的 coding agent：

```bash
governspec compile govern.yaml --target agents-md --out AGENTS.md
```

编译给 Claude Code：

```bash
governspec compile govern.yaml --target claude-md --out CLAUDE.md
```

编译给 Cursor：

```bash
governspec compile govern.yaml --target cursor-rules --out .
```

编译给 OpenAI Structured Outputs：

```bash
governspec compile govern.yaml --target openai-structured --out task.openai-structured.json
```

### 5. 让 agent 工作

在 Cursor、Codex、Claude Code 或你的 API workflow 中正常运行 agent。GovernSpec 不接管这一步，它只提供目标工具能读取的 artifact。

### 6. 验收输出

把 agent 输出保存成文件，例如 `output.md`：

```bash
governspec test govern.yaml --output output.md
```

输出示例：

```text
Test status: ok
Passed:
- Must include all sections [required_sections]: All required sections are present.
- Must stay concise [max_words]: Estimated word count is within limit.
Failed: none
```

## 不想手写 YAML

### 从自然语言生成草稿

```bash
governspec draft "Review this repository without modifying code" --out draft.govern.yaml
governspec draft "帮我做客户会议简报，不要泄露隐私，涉及敏感数据先问我" --out draft.govern.yaml
```

`draft` 是本地启发式生成，不调用真实模型。它适合冷启动，但生成后仍然应该人工 review。

### 从已有 artifact 导入

```bash
governspec import AGENTS.md --out imported.govern.yaml
governspec import CLAUDE.md --out imported.govern.yaml
governspec import .cursor/rules/project.mdc --out imported.govern.yaml
governspec import task.openai-structured.json --out imported.govern.yaml
```

支持的导入来源：

| Source | Auto-detect 依据 |
| --- | --- |
| `agents-md` | `AGENTS.md` 文件名 |
| `claude-md` | `CLAUDE.md` 文件名 |
| `cursor-rules` | `.mdc` 扩展名 |
| `openai-structured` | `json_schema` key |
| `gemini-structured` | `generationConfig` key |

导入结果是 draft，不是等价证明。自然语言 artifact 一定存在信息损失，所以导入后建议运行 `governspec validate` 和 `governspec inspect`。

## GovernPack 复用治理规则

通用规则可以写成 `GovernPack`：

```yaml
# packs/privacy.govern.yaml
version: "0.1"
kind: "GovernPack"

metadata:
  name: "privacy_pack"
  description: "Privacy and PII protection rules"

constraints:
  - "Do not expose personal data."

permissions:
  web: false
  network: false

human_gates:
  - when: "Sensitive personal data is involved"
    action: "ask_confirmation"
```

任务 contract 中引用：

```yaml
imports:
  - "./packs/privacy.govern.yaml"
```

导入合并规则是保守的：

- 标量字段本地优先。
- 列表合并去重。
- 权限取更严格结果，deny wins。
- 导入的 acceptance assertions 不会被本地同名测试静默覆盖。

## 编译目标

| Target | 用途 | 输出 |
| --- | --- | --- |
| `prompt` | 通用 Markdown prompt | 文本 |
| `agents-md` | Codex 或 repository instruction workflow | `AGENTS.md` |
| `claude-md` | Claude Code project memory | `CLAUDE.md` |
| `cursor-rules` | Cursor Project Rules | `.cursor/rules/governspec.mdc` |
| `antigravity-rules` | Antigravity-compatible repository rules | `.agents/rules/governspec.md` |
| `skill` | 通用 skill bundle | `SKILL.md`、`references/`、`scripts/` |
| `openai-structured` | OpenAI Structured Outputs | JSON payload |
| `gemini-structured` | Gemini structured output | JSON payload |
| `mcp-plan` | MCP planning / inspection | JSON with risk and constraint loss |
| `openai-json` | Legacy transition payload | JSON payload |

完整集成说明见 [docs/integrations.md](docs/integrations.md)，其中列出了每类
GovernSpec 产物的目标工具和落地方式。

## 输出验收断言

`governspec test` 支持以下 deterministic assertion：

| Assertion | 检查内容 |
| --- | --- |
| `required_sections` | Markdown 输出是否包含 `output.sections` 定义的所有章节 |
| `contains` | 输出是否包含指定文本 |
| `not_contains` | 输出是否不包含禁止文本 |
| `regex` | 输出是否匹配指定正则 |
| `no_regex` | 输出是否不匹配禁止正则 |
| `max_words` | 字数是否在 `output.max_words` 限制内 |
| `max_chars` | 字符数是否在限制内 |
| `json_schema` | JSON 输出是否符合 `output.schema` |
| `json_path_exists` | JSON 中指定路径是否存在 |
| `json_array_min_items` | JSON array 是否满足最少元素数 |

这些断言适合验证格式、结构、长度和显式文本规则。它们不验证复杂事实真伪，也不能替代人工审查。

## 常见工作流

### 代码审查

```bash
governspec examples --copy code_review.govern.yaml --out code_review.govern.yaml
governspec validate code_review.govern.yaml
governspec compile code_review.govern.yaml --target agents-md --out AGENTS.md
governspec test code_review.govern.yaml --output review.md
```

适合限制 agent 只读仓库、输出固定章节、不修改文件。

### 结构化 JSON 报告

```bash
governspec examples --copy report_json.govern.yaml --out report_json.govern.yaml
governspec compile report_json.govern.yaml --target openai-structured --out task.openai-structured.json
governspec test report_json.govern.yaml --output report_json.output.json
```

适合 API workflow、machine-readable report 和 CI 检查。

### 多工具规则同步

```bash
governspec compile govern.yaml --target agents-md --out AGENTS.md
governspec compile govern.yaml --target claude-md --out CLAUDE.md
governspec compile govern.yaml --target cursor-rules --out .
```

适合同一仓库中并行使用 Codex、Claude Code 和 Cursor 的团队。

### CI 检查

```bash
governspec validate govern.yaml
governspec compile govern.yaml --target agents-md --out /tmp/AGENTS.md
governspec test govern.yaml --output output.md
```

建议在 CI 中至少检查重要 contracts 能否 validate 和 compile。

## MCP Server

GovernSpec 提供薄 MCP server：

```bash
governspec-mcp
```

暴露的 tools：

- `governspec.validate`
- `governspec.inspect`
- `governspec.compile`
- `governspec.test`

暴露的 resources：

- `govern://spec/<path>`
- `govern://iir/<path>`
- `govern://compiled/<target>/<path>`

`governspec-mcp` 是集成面，不是 runtime orchestration platform。

## Python SDK

常用 document-level API：

```python
from pathlib import Path
from governspec_core import (
    load_document,
    resolve_document_imports,
    inspect_document,
    validate_document,
    compile_target,
    test_output,
    import_from_artifact,
    import_from_string,
    heuristic_draft_payload,
)

document = load_document(Path("govern.yaml"))
resolved = resolve_document_imports(document, Path("."))
report = validate_document(resolved)
payload = inspect_document(resolved)
```

如果只处理 `GovernSpec`，也可以使用更窄的 `load_spec`、`resolve_imports` 和 `validate_spec`。

## 仓库结构

```text
packages/governspec-core/   schema、parser、IIR、imports、targets、testing
packages/governspec-cli/    Typer CLI, governspec command
packages/governspec-mcp/    thin MCP server
packages/governspec-ts/     TypeScript package MVP
packages/governspec-vscode/ VS Code extension MVP
examples/                   runnable example contracts and outputs
schema/                     generated JSON Schema
benchmark/                  offline benchmark artifacts
docs/                       technical docs, migration guide, release notes
tests/                      pytest test suite
```

## 文档索引

- [docs/technical-guide.md](docs/technical-guide.md), 详细技术指南，推荐新用户阅读。
- [docs/integrations.md](docs/integrations.md), 各工具集成方式。
- [docs/iir.md](docs/iir.md), 中间表示 IIR 设计。
- [docs/engineering/repository_file_map_zh.md](docs/engineering/repository_file_map_zh.md), 仓库关键文件地图。
- [docs/migration-v0.1.md](docs/migration-v0.1.md), 迁移到 v0.1 schema。
- [docs/project-roadmap-zh.md](docs/project-roadmap-zh.md), 项目从 0% 到 100% 的总规划和当前进度。
- [benchmark.md](benchmark.md), benchmark 使用说明。
- [failure-cases.md](failure-cases.md), 已知失败案例和边界。

## Benchmark

运行基础 benchmark：

```bash
python benchmark/run_benchmark.py
```

Benchmark 不调用真实 LLM，只评估本地 artifacts、compile behavior、round-trip import 和 deterministic tests。

## 开发

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy
```

构建发布包：

```bash
python -m build
twine check dist/*
```

贡献前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。安全问题请按
[SECURITY.md](SECURITY.md) 私下报告。行为准则见
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

如果你在研究中使用 GovernSpec，请使用 [CITATION.cff](CITATION.cff) 中的
元数据引用本软件。

## 路线图

### v0.2

- 更高质量的 draft generation。
- 更细的 assertion auto-selection。
- 更完整的 round-trip fidelity tests。
- 更清晰的 target capability diagnostics。

### v0.3+

- Pack registry。
- Import trace。
- Workflow-level contract composition。
- IDE diagnostics。
- 可选 model-based semantic evaluation。

## License

MIT. See [LICENSE](LICENSE).
