# IntentSpec

IntentSpec 是一个离线契约编译器，用来统一管理 AI agent 的任务规则。

你维护一份 `intent.yaml`，IntentSpec 帮你编译成各家工具能读的格式：

```
            ┌─────────────┐
            │ intent.yaml │  ← 唯一源文件
            └──────┬──────┘
                   │
            IntentSpec 编译
                   │
       ┌───────┬───┴───┬────────┐
       ▼       ▼       ▼        ▼
   Cursor   Codex   Claude   OpenAI/Gemini
    .mdc   AGENTS.md CLAUDE.md  JSON
```

一份契约里可以定义：

- 任务目标（goal）
- 权限边界（permissions）
- 人工确认门（human gates）
- 结构化输出（structured outputs）
- 验收测试（acceptance tests）

> Define once, validate and compile everywhere.

IntentSpec 不是 agent runtime，不调用真实 LLM，不替代 MCP、Codex、Claude Code 或其他编排框架。它只做编译和验收。

## 安装

要求 Python >= 3.11，不需要 API key，不联网。

```bash
# 普通安装
pip install intentspec

# 开发模式（含 pytest, ruff, mypy 等）
pip install -e ".[dev]"
```

验证安装：

```bash
intent doctor
```

## 快速开始：5 步走完整流程

### 1. 创建契约

```bash
intent init
```

这会生成 `intent.yaml` 模板。打开编辑，写入你的任务要求：

```yaml
version: "0.1"
kind: "IntentSpec"

metadata:
  name: "code_review"
  title: "代码审查报告"
  owner: "dev-team"

task:
  goal: "审查代码库，输出问题报告，不修改任何代码"
  priority: "high"

permissions:
  web: false
  filesystem:
    read: true
    write: false
  network: false
  tools:
    send_email: false
    delete_file: false
    purchase: false

constraints:
  - "不要捏造事实"
  - "不要修改已有代码"

human_gates:
  - when: "发现高危安全问题"
    action: "ask_confirmation"

output:
  format: "markdown"
  language: "zh-CN"
  max_words: 800
  sections:
    - "整体评估"
    - "必须修复"
    - "改进建议"
    - "测试建议"

tests:
  - name: "必须包含所有章节"
    assert:
      - type: "required_sections"
  - name: "字数不超标"
    assert:
      - type: "max_words"
```

### 2. 验证契约

```bash
intent validate intent.yaml
```

输出 `Validation status: ok` 表示契约合法。

### 3. 编译到目标平台

```bash
# 编译成 Cursor Rules
intent compile intent.yaml --target cursor-rules --out .
# 生成 .cursor/rules/intentspec.mdc

# 编译成 AGENTS.md（给 Codex）
intent compile intent.yaml --target agents-md --out AGENTS.md

# 编译成 CLAUDE.md（给 Claude Code）
intent compile intent.yaml --target claude-md --out CLAUDE.md
```

编译完成后，各工具会自动读取对应文件，你不需要手动贴 prompt。

### 4. 让 agent 工作，生成产出

在 Cursor / Codex / Claude Code 里正常对话。agent 会遵守编译好的规则。

把 agent 的产出保存为文件（如 `output.md`）。

### 5. 验收产出

```bash
intent test intent.yaml --output output.md
```

输出示例：

```
Test status: ok
Passed:
- 必须包含所有章节 [required_sections]: All required sections are present.
- 字数不超标 [max_words]: Estimated word count 650 is within limit 800.
Failed: none
```

**这就是完整流程：写契约 → 验证 → 编译 → agent 工作 → 验收。**

## 其他入口：不想手写 YAML

### 用自然语言生成草稿

```bash
intent draft "帮我做一份客户会议简报，别泄露隐私，必要时先问我"
intent draft "Review this codebase without modifying code" --out draft.intent.yaml
```

支持中英文。会自动推断权限、约束、人工确认门、输出格式和 sections。

### 从已有产物反向导入

已经有 `AGENTS.md`、Cursor Rules 或 structured output JSON？直接导入：

```bash
intent import AGENTS.md --out imported.intent.yaml
intent import .cursor/rules/my-rules.mdc --out imported.intent.yaml
intent import task.openai-structured.json --out imported.intent.yaml
```

支持 5 种来源：`agents-md`、`claude-md`、`cursor-rules`、`openai-structured`、`gemini-structured`。`--type` 可省略，CLI 会自动推断。

## IntentPack：复用治理规则

把通用约束抽成 pack，跨任务复用：

```yaml
# packs/privacy.intent.yaml
version: "0.1"
kind: "IntentPack"

metadata:
  name: "privacy_pack"
  description: "隐私和 PII 防护规则"

constraints:
  - "不得暴露个人隐私数据"

human_gates:
  - when: "涉及隐私敏感信息"
    action: "ask_confirmation"
```

在任务契约里引用：

```yaml
imports:
  - "./packs/privacy.intent.yaml"
  - "./packs/no-network.intent.yaml"
```

导入合并规则：标量本地优先，列表合并去重，权限取最严（deny wins）。

## 编译目标


| 目标                  | 用途                        | 输出                                      |
| ------------------- | ------------------------- | --------------------------------------- |
| `prompt`            | 通用 Markdown prompt        | 文本                                      |
| `agents-md`         | Codex / coding agents 指令  | `AGENTS.md`                             |
| `claude-md`         | Claude Code 指令            | `CLAUDE.md`                             |
| `cursor-rules`      | Cursor 项目规则               | `.cursor/rules/intentspec.mdc`          |
| `antigravity-rules` | Antigravity 规则            | `.agents/rules/intentspec.md`           |
| `skill`             | 通用 skill bundle           | `SKILL.md` + `references/` + `scripts/` |
| `openai-structured` | OpenAI Structured Outputs | JSON payload                            |
| `gemini-structured` | Gemini structured output  | JSON payload                            |
| `mcp-plan`          | MCP 安全执行计划                | JSON（含 `risk_level`、`constraint_loss`）  |
| `openai-json`       | legacy 过渡目标               | JSON payload                            |


`skill` 是通用 bundle，不限定特定工具链。Codex、Claude Code、Cursor、VS Code Agent、Antigravity 等基于仓库文件承载规则的工作流都可以直接使用。

## 命令参考

### `intent init`

```bash
intent init
intent init --file my-task.intent.yaml
```

在当前目录生成 `intent.yaml` 模板。如果文件已存在，拒绝覆盖。

### `intent validate`

```bash
intent validate intent.yaml
intent validate intent.yaml --format json
```

### `intent inspect`

```bash
intent inspect intent.yaml
intent inspect intent.yaml --format json
```

输出归一化后的中间表示（IIR）。对 `IntentSpec` 输出完整合并后的视图，对 `IntentPack` 输出 pack 视图。

### `intent compile`

```bash
intent compile intent.yaml --target agents-md --out AGENTS.md
intent compile intent.yaml --target openai-structured --out task.json
intent compile intent.yaml --target cursor-rules --out .
intent compile intent.yaml --target skill --out ./review-skill
intent compile intent.yaml --target mcp-plan
```

### `intent test`

```bash
intent test intent.yaml --output output.md
intent test intent.yaml --output output.json --format json
```

支持的断言类型：


| 断言                     | 检查内容                             |
| ---------------------- | -------------------------------- |
| `required_sections`    | 产出是否包含 `output.sections` 定义的所有章节 |
| `contains`             | 产出是否包含指定文本                       |
| `not_contains`         | 产出是否不包含禁止文本                      |
| `regex`                | 产出是否匹配正则                         |
| `no_regex`             | 产出是否不匹配禁止正则                      |
| `max_words`            | 字数是否在 `output.max_words` 限制内     |
| `max_chars`            | 字符数是否在限制内                        |
| `json_schema`          | JSON 产出是否符合 `output.schema`      |
| `json_path_exists`     | JSON 中指定路径是否存在                   |
| `json_array_min_items` | JSON 数组是否满足最少元素数                 |


所有断言都是确定性的、离线的，不调用模型。

### `intent draft`

```bash
intent draft "帮我做一份客户会议简报，别泄露隐私，必要时先问我"
intent draft "Review this repository without modifying code" --out draft.intent.yaml
```

- 实验性功能（`experimental`）
- 支持中英文
- 不调用真实模型，纯启发式推断

### `intent import`

```bash
intent import AGENTS.md --out imported.intent.yaml
intent import CLAUDE.md --type claude-md --out imported.intent.yaml
intent import .cursor/rules/intentspec.mdc --out imported.intent.yaml
intent import task.openai-structured.json --out imported.intent.yaml
intent import task.gemini-structured.json --type gemini-structured --out imported.intent.yaml
```

- `--type` 可省略，自动推断
- `--out` 不覆盖已有文件
- 对 IntentSpec 编译产出精确还原，对手写文档启发式解析

### `intent workflow`

一键执行完整工作流（validate → compile → test）：

```bash
intent workflow
intent workflow --workdir ./my-project --init --skip-test
```


| 参数                        | 默认值                           | 说明                          |
| ------------------------- | ----------------------------- | --------------------------- |
| `--workdir`               | `.`                           | 工作目录                        |
| `--intent-file`           | `intent.yaml`                 | 契约文件路径                      |
| `--prompt-out`            | `task.prompt.md`              | prompt 编译输出                 |
| `--openai-structured-out` | `task.openai-structured.json` | OpenAI JSON 编译输出（仅 JSON 任务） |
| `--agents-out`            | `AGENTS.md`                   | AGENTS.md 编译输出              |
| `--mcp-plan-out`          | `task.mcp-plan.json`          | MCP plan 编译输出               |
| `--output-file`           | 按格式自动选择                       | agent 产出文件路径                |
| `--init`                  | `false`                       | 先创建 intent.yaml 再执行         |
| `--skip-test`             | `false`                       | 跳过验收测试步骤                    |


### `intent doctor`

```bash
intent doctor
intent doctor --format json
```

检查 Python 版本、IntentSpec 包版本、当前目录是否有 `intent.yaml`、JSON Schema 是否可生成。

### `intent examples`

```bash
intent examples
intent examples --copy customer_brief.intent.yaml --out ./customer_brief.intent.yaml
intent examples --copy packs/privacy.intent.yaml --out ./packs/privacy.intent.yaml
```

### `intent schema`

```bash
intent schema
intent schema --out schema/intentspec.schema.json
```

导出当前版本的 JSON Schema。

## 集成矩阵


| 工具 / 生态       | 接入路径                      | IntentSpec 产物                                          |
| ------------- | ------------------------- | ------------------------------------------------------ |
| Codex         | 仓库指令 + skills + MCP       | `agents-md`、`skill`、`intentspec-mcp`                   |
| Claude Code   | 指令文件 + MCP                | `claude-md`、`skill`、`intentspec-mcp`                   |
| Cursor        | 项目规则 + MCP                | `cursor-rules`、`skill`、`intentspec-mcp`                |
| VS Code Agent | 项目指令 + MCP + 扩展           | `agents-md`、`skill`、`intentspec-mcp`、VS Code extension |
| OpenAI API    | structured output payload | `openai-structured`                                    |
| Gemini API    | structured output payload | `gemini-structured`                                    |
| Antigravity   | 文件系统规则 + MCP              | `antigravity-rules`、`skill`、`intentspec-mcp`           |


完整说明见 [docs/integrations.md](docs/integrations.md)。

## MCP Server

IntentSpec 提供薄 MCP server，让 MCP 客户端（Cursor、Claude Code 等）直接调用：

```bash
intentspec-mcp
```

暴露的 tools：`intentspec.validate`、`intentspec.inspect`、`intentspec.compile`、`intentspec.test`

暴露的 resources：`intent://spec/<path>`、`intent://iir/<path>`、`intent://compiled/<target>/<path>`

它只提供集成面，不实现 runtime orchestration。

## Python SDK

```python
from intentspec_core import (
    # 核心流程
    load_document,
    validate_document,
    compile_target,
    inspect_document,
    test_output,
    resolve_document_imports,
    # 反向导入
    SUPPORTED_IMPORT_TYPES,
    import_from_artifact,
    import_from_string,
    # 草稿生成
    heuristic_draft_payload,
)
```

反向导入示例：

```python
from pathlib import Path
from intentspec_core import import_from_artifact, import_from_string

payload = import_from_artifact(Path("AGENTS.md"))
payload = import_from_string(json_text, "openai-structured")
```

如果只处理 `IntentSpec`（不含 `IntentPack`），也可以使用 `load_spec`、`resolve_imports`、`validate_spec`。

## 仓库结构

```text
packages/intentspec-core/   解析器、导入、IIR、编译器、测试器、SDK
packages/intentspec-cli/    Typer CLI（intent 命令）
packages/intentspec-mcp/    薄 MCP server
packages/intentspec-ts/     TypeScript 轻量封装
packages/intentspec-vscode/ VS Code 扩展 MVP
examples/                   示例契约和样例输出
schema/                     生成的 JSON Schema
benchmark/                  离线 benchmark
docs/                       设计、迁移、发布文档
tests/                      pytest 测试套件（210 tests）
```

## Benchmark

离线 benchmark，不调用真实 LLM，只对已有产物运行验收测试：

```bash
python benchmark/run_benchmark.py
```

覆盖 markdown task、JSON schema task、imported pack task、`constraint_loss` 观察项。

文档模板见 [benchmark.md](benchmark.md)。

## 迁移

如果你有早期草稿或内部原型需要对齐到 v0.1 schema：

1. 用 `intent import` 导入已有产物（如 `AGENTS.md`、Cursor Rules）
2. 将 `version` 设为 `"0.1"`
3. 抽取共享约束为 `IntentPack`
4. JSON 任务改用 `output.schema`
5. 运行 `intent validate` + `intent test` 验证

详见 [docs/migration-v0.1.md](docs/migration-v0.1.md)。

## 非目标

v0.1 明确不做：

- 真实 LLM runtime
- Web UI
- 数据库
- LangGraph / DSPy / BAML adapter
- MCP orchestration platform
- 自动高权限动作执行

## 路线图

### v0.2（规划中）

- LLM-backed draft generation：可选接入模型生成更高质量的 `intent.yaml` 草稿
- assertion type auto-selection：导入时根据测试名称自动选择合适的断言类型（如 `json_schema` vs `required_sections`）
- CJK-aware text truncation：中文截断在语义边界断开，而非硬切字符
- round-trip fidelity tests：compile → import → compile 全链路保真度测试

### v0.3（规划中）

- pack registry：远程 pack 注册中心，支持 `imports` 引用远程 pack
- import trace：IIR 中记录完整的导入来源链，便于审计
- target capability analysis：编译时详细报告每个目标的能力缺失
- stricter migration tooling：自动化 schema 版本迁移工具

### v0.4（规划中）

- workflow-level contract composition：多个 `intent.yaml` 组成工作流级别的契约链
- richer benchmark suites：更多任务类型、更多目标的 benchmark 覆盖
- IDE integrations：Cursor / VS Code 深度集成（补全、inline diagnostics）
- permission review surfaces：可视化权限审计面板
- model-based output evaluation：可选接入模型做语义层面的产出评估

## 发布检查

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy
python -m build
twine check dist/*
```

完整清单见 [docs/release-checklist.md](docs/release-checklist.md)。