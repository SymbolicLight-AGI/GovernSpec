# GovernSpec 技术指南

GovernSpec 是一个本地优先的 AI 任务契约工具。它解决的问题不是“再做一个 agent
runtime”，而是把分散在 `AGENTS.md`、`CLAUDE.md`、Cursor Rules、Structured
Outputs 和 MCP 计划里的任务要求，统一收敛到一份可审查、可编译、可验收的
`govern.yaml`。

一句话概括：

> GovernSpec 让团队用一份任务契约定义目标、权限、约束、人工确认门、输出格式和验收测试，然后编译到多个 AI 工具，并在产出后做离线检查。

## 1. 这份文档适合谁

### AI 应用开发者

如果你正在把 LLM 或 coding agent 接入真实产品，通常会遇到这些问题：

- 不同工具需要不同格式的 instructions、rules 或 schema。
- 同一套安全要求需要在多个地方重复维护。
- prompt 很难 code review，因为它经常是自然语言长文本。
- 结构化输出失败后，很难判断是模型问题、schema 问题还是提示词漂移。

GovernSpec 可以把这些要求放进 `govern.yaml`，再编译成目标平台需要的文件或 JSON
payload。

### 使用 Cursor、Codex、Claude Code 的工程团队

如果团队同时使用多种 AI coding 工具，GovernSpec 可以作为上游规则源。你不需要为每个工具手写一份规则，而是维护一份 contract：

- 给 Codex 或其他读取 repository instructions 的工具，编译成 `AGENTS.md`。
- 给 Claude Code，编译成 `CLAUDE.md`。
- 给 Cursor，编译成 `.cursor/rules/governspec.mdc`。
- 给 structured output API，编译成 OpenAI 或 Gemini 的 JSON payload。

这样团队 review 的对象从多个工具文件变成一份源契约。

### 平台治理、安全和合规负责人

如果你关心 AI agent 的权限边界、人工确认、隐私和输出质量，GovernSpec 可以把这些内容变成显式字段，而不是埋在 prompt 里：

- `permissions` 描述能不能联网、读写文件、调用高风险工具。
- `constraints` 描述必须遵守的规则。
- `human_gates` 描述什么时候必须让人确认。
- `evidence` 描述事实、推断、不确定性的处理方式。
- `tests` 描述最终输出必须通过哪些离线检查。

这让治理要求更适合审查、复用和持续集成。

### 研究者和工具作者

GovernSpec 也适合做 AI agent 工具链研究。它提供：

- 一个显式 task contract schema。
- 一个中间表示 IIR，用于观察导入合并、权限收紧和 target capability loss。
- 一个可复现 benchmark，用于评估编译覆盖、round-trip fidelity 和 offline assertion。
- 多个导入器，用于把已有 instructions 或 structured output payload 迁移回 contract。

## 2. 不适合谁

GovernSpec 有明确边界，避免把能力说过头：

- 它不是 LLM runtime。
- 它不调用真实 LLM API。
- 它不替代 MCP、Cursor、Codex、Claude Code 或其他 agent 框架。
- 它不能保证 agent 在运行时一定不会违规。
- 它不是权限沙箱，也不是 runtime policy enforcement system。

GovernSpec 做的是 artifact-level governance：编译规则、迁移规则、检查输出。真正的运行时权限控制仍然需要由操作系统、agent runtime、MCP server、CI/CD 或企业安全系统承担。

## 3. 你能得到什么

### 一份可审查的 AI 任务契约

过去团队可能把任务规则写在 prompt、README、Cursor Rules、Claude memory、API
schema 和 CI 脚本里。GovernSpec 把它们统一到一个 `govern.yaml`：

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

这份文件可以进入 Git，接受 code review，并随项目演进。

### 多平台目标文件

同一份 contract 可以编译为多种目标：

| Target | 适用场景 | 输出 |
| --- | --- | --- |
| `agents-md` | Codex 或读取 `AGENTS.md` 的 coding agent | `AGENTS.md` |
| `claude-md` | Claude Code 项目指令 | `CLAUDE.md` |
| `cursor-rules` | Cursor Project Rules | `.cursor/rules/governspec.mdc` |
| `openai-structured` | OpenAI Structured Outputs | JSON schema payload |
| `gemini-structured` | Gemini structured output | JSON payload |
| `mcp-plan` | MCP planning / inspection | Machine-readable plan |
| `prompt` | 通用 prompt 预览 | Markdown text |
| `skill` | 通用 skill bundle | `SKILL.md` 等文件 |

### 可复用治理包

通用规则可以写成 `GovernPack`，让多个任务复用：

```yaml
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
```

任务里引用：

```yaml
imports:
  - "./packs/privacy.govern.yaml"
```

GovernSpec 会解析 imports，并按保守规则合并：权限取更严格结果，列表合并去重，导入的测试断言不会被本地同名测试静默覆盖。

### 离线验收报告

GovernSpec 可以在 agent 产出之后做 deterministic checks：

```bash
governspec test govern.yaml --output output.md
```

典型输出：

```text
Test status: ok
Passed:
- Must include all sections [required_sections]: All required sections are present.
- Must stay concise [max_words]: Estimated word count is within limit.
Failed: none
```

如果输出缺章节、包含禁用内容、超过长度限制、JSON schema 不匹配，测试会失败。这样你可以把 AI 产出接入 CI，至少保证格式和一部分合规要求稳定。

## 4. 安装和环境要求

GovernSpec v0.1 需要 Python 3.11+。

从 PyPI 安装：

```bash
pip install governspec
```

从源码开发安装：

```bash
pip install -e ".[dev]"
```

检查环境：

```bash
governspec doctor
```

运行测试：

```bash
pytest
```

GovernSpec 的核心流程不需要 API key，不需要联网，也不会调用真实 LLM。

## 5. 最小使用流程

### 第一步：创建 contract

```bash
governspec init
```

中文用户可以生成中文占位说明：

```bash
governspec init --locale zh-CN
```

这会生成默认 `govern.yaml`。你可以修改 `goal`、`permissions`、`constraints`、
`output` 和 `tests`。

### 第二步：验证 contract

```bash
governspec validate govern.yaml
```

如果契约合法，会得到 `Validation status: ok`。如果字段类型错误、权限配置不合法、输出格式缺失，验证会失败。

### 第三步：查看规范化结果

```bash
governspec inspect govern.yaml
```

如果要给脚本或 CI 使用：

```bash
governspec inspect govern.yaml --format json
```

`inspect` 展示的是 import 解析和 normalization 之后的 IIR。它适合用来审查最终权限、约束和测试是否符合预期。

### 第四步：编译到目标工具

编译为 `AGENTS.md`：

```bash
governspec compile govern.yaml --target agents-md --out AGENTS.md
```

编译为 `CLAUDE.md`：

```bash
governspec compile govern.yaml --target claude-md --out CLAUDE.md
```

编译为 Cursor Rules：

```bash
governspec compile govern.yaml --target cursor-rules --out .
```

编译为 OpenAI Structured Outputs：

```bash
governspec compile govern.yaml --target openai-structured --out task.openai-structured.json
```

编译为 Gemini structured output：

```bash
governspec compile govern.yaml --target gemini-structured --out task.gemini-structured.json
```

### 第五步：让 agent 工作

在目标工具里正常使用 agent。GovernSpec 不接管 agent runtime，它只是生成目标工具能读取的 artifact。

例如：

- Codex 读取 `AGENTS.md`。
- Claude Code 读取 `CLAUDE.md`。
- Cursor 读取 `.cursor/rules/governspec.mdc`。
- API 调用使用 structured output JSON payload。

### 第六步：验收输出

把 agent 输出保存为文件，然后运行：

```bash
governspec test govern.yaml --output output.md
```

对于 JSON 输出：

```bash
governspec test report_json.govern.yaml --output output.json
```

## 6. 不想手写 YAML 怎么办

### 从自然语言生成草稿

```bash
governspec draft "Review this codebase without modifying files and produce a concise report." --out draft.govern.yaml
```

中文也可以：

```bash
governspec draft "帮我写客户会议简报，不要泄露隐私，涉及敏感数据先问我" --out draft.govern.yaml
```

`draft` 是启发式生成，不调用 LLM。它适合冷启动，但生成后仍然应该人工 review。

### 从已有 artifact 反向导入

如果你已经有 `AGENTS.md`、`CLAUDE.md`、Cursor Rules 或 structured output JSON，可以导入成 contract 草稿：

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

导入结果是 draft，不是严格等价证明。自然语言 artifact 的导入一定存在启发式判断，所以导入后应该运行 `governspec validate` 和 `governspec inspect`，再由人确认。

## 7. 典型落地场景

### 场景一：代码审查

团队希望 agent 审查代码但不改文件：

- `permissions.filesystem.read = true`
- `permissions.filesystem.write = false`
- `constraints` 写明不要修改代码、不要捏造事实
- `output.sections` 固定为 `Summary`、`Findings`、`Testing`
- `tests` 使用 `required_sections` 和 `max_words`

得到的结果：

- Codex、Claude Code、Cursor 可以共享同一组审查规则。
- 输出缺章节或太长时，`governspec test` 会失败。
- 规则变更可以通过 Git review。

### 场景二：客户简报

团队希望 agent 生成客户简报，但不泄露隐私：

- 引入 `privacy_pack`
- 禁止 network 和 web
- 对 confidential input 加 human gate
- 输出语言设为 `zh-CN`
- 验收测试要求包含固定 sections，且不能出现 forbidden pattern

得到的结果：

- 隐私规则在多个任务中复用。
- 客户简报输出更稳定。
- 敏感场景下是否需要人工确认变成显式规则。

### 场景三：结构化 JSON 报告

团队希望 LLM 输出机器可解析 JSON：

- `output.format = "json"`
- `output.json_schema` 定义 schema
- 编译到 `openai-structured` 或 `gemini-structured`
- 使用 `json_schema`、`json_path_exists`、`json_array_min_items` 做验收

得到的结果：

- API 侧可以使用 structured output payload。
- 本地 CI 可以复查 JSON 结构。
- 不同 provider 的 schema 限制会在 compile 阶段暴露，而不是在运行时静默丢失。

### 场景四：已有 prompt 迁移

团队已经有多年积累的 `AGENTS.md`、`CLAUDE.md` 或 Cursor Rules：

```bash
governspec import AGENTS.md --out migrated.govern.yaml
governspec inspect migrated.govern.yaml
governspec compile migrated.govern.yaml --target cursor-rules --out .
```

得到的结果：

- 老规则可以迁移成结构化 contract。
- 多平台规则可以重新从同一个 source-of-truth 编译。
- 迁移中的信息损失可以通过 inspect 和 round-trip review 暴露。

## 8. CI/CD 用法

最简单的 CI 检查可以包含三类：

```bash
governspec validate govern.yaml
governspec compile govern.yaml --target agents-md --out /tmp/AGENTS.md
governspec test govern.yaml --output output.md
```

建议的策略：

- 对每个重要 `govern.yaml` 运行 `governspec validate`。
- 对团队实际使用的 targets 运行 `governspec compile`，防止 schema 或 target capability 变化导致编译失败。
- 对示例输出或 golden outputs 运行 `governspec test`。
- 对导入后的 draft 运行 `governspec inspect --format json`，保存 review artifact。

## 9. 与 MCP 的关系

GovernSpec 提供一个薄 MCP server：

```bash
governspec-mcp
```

它暴露：

- `governspec.validate`
- `governspec.inspect`
- `governspec.compile`
- `governspec.test`

也暴露资源：

- `govern://spec/<path>`
- `govern://iir/<path>`
- `govern://compiled/<target>/<path>`

MCP 集成的用途是让 MCP-capable clients 直接读取和使用 GovernSpec 的 validation、inspection、compilation 和 testing 能力。它不是通用文件读取服务，路径访问应限制在项目工作区内。

## 10. 输出验收支持哪些断言

当前支持 10 类 deterministic assertion：

| Assertion | 用途 |
| --- | --- |
| `required_sections` | 检查 markdown 输出是否包含所有要求章节 |
| `contains` | 检查输出必须包含某些文本 |
| `not_contains` | 检查输出不能包含某些文本 |
| `regex` | 检查输出必须匹配正则 |
| `no_regex` | 检查输出不能匹配正则 |
| `max_words` | 检查最大词数 |
| `max_chars` | 检查最大字符数 |
| `json_schema` | 检查 JSON schema |
| `json_path_exists` | 检查 JSON path 是否存在 |
| `json_array_min_items` | 检查 JSON array 最少元素数 |

这些断言适合验证格式、结构、长度和显式文本规则。它们不适合验证复杂事实真伪，也不能替代人工审查。

## 11. 设计原则

### Local-first

GovernSpec 默认本地运行，不要求真实 LLM、不要求 API key、不要求联网。这让它适合进入 CI、研究 benchmark 和企业内网环境。

### Zero-intrusion

GovernSpec 不要求下游 agent runtime 改造。它通过现有 artifact channel 集成：markdown instructions、rules 文件、structured output JSON 和 MCP surface。

### Source-of-truth

`govern.yaml` 是唯一源文件。下游文件是编译结果，不应该手动长期维护。如果需要改规则，先改 contract，再重新 compile。

### Conservative governance

权限合并采用更保守的方向。例如导入 pack 禁止 network，本地 contract 不应该因为疏忽而放宽它。导入的 acceptance assertions 也不应该被同名本地测试静默覆盖。

### Deterministic validation

验收测试只做确定性检查，避免把主观语义判断伪装成严格验证。

## 12. 局限与风险

### 编译不是执行保证

编译出 `AGENTS.md` 或 Cursor Rules 不等于 agent 一定会遵守。GovernSpec 帮你把规则放到正确位置，并在输出后检查一部分可验证约束，但不能控制模型内部行为。

### 自然语言导入有损

从 `AGENTS.md` 或 `CLAUDE.md` 反向导入时，工具只能做启发式恢复。复杂、含糊或隐含的规则可能无法完整还原。

### Structured output 目标有能力边界

`openai-structured` 和 `gemini-structured` 适合 JSON schema 输出，但不能表达所有自然语言约束、human gates 或 evidence policy。GovernSpec 会尽量在编译时暴露这些 target limitation。

### Regex 需要谨慎

正则断言适合简单模式，不建议写复杂、不可维护的表达式。GovernSpec 对正则执行做了超时保护，但规则作者仍应保持模式简单。

## 13. 最佳实践

- 每个重要 agent 任务都维护一份 `govern.yaml`。
- 把跨任务规则抽成 `GovernPack`。
- 把生成的 `AGENTS.md`、`CLAUDE.md`、Cursor Rules 视为 build artifact。
- 在 PR 中 review `govern.yaml`，不要只 review 编译后的 markdown。
- 对关键输出样本维护 golden output，并用 `governspec test` 放进 CI。
- 对 structured output 任务优先写明确 `json_schema`。
- 对高风险权限使用 `human_gates`。
- 对导入结果一定运行 `governspec inspect` 并人工确认。

## 14. 开源包里有什么

开源仓库主要目录：

| 路径 | 内容 |
| --- | --- |
| `packages/governspec-core` | schema、parser、IIR、imports、targets、testing |
| `packages/governspec-cli` | `governspec` CLI |
| `packages/governspec-mcp` | MCP server |
| `packages/governspec-ts` | TypeScript package MVP |
| `packages/governspec-vscode` | VS Code extension MVP |
| `examples/` | 可运行示例 |
| `schema/` | JSON schema |
| `benchmark/` | benchmark 和 ICSE paper 实验包 |
| `docs/` | 文档、论文草稿和 release notes |
| `tests/` | 测试 |

如果你只想快速试用，从 `examples/` 开始。如果你想理解架构，从 `docs/iir.md` 和
`docs/integrations.md` 开始。如果你想复现实验，从 `benchmark/paper_icse2027/README.md` 开始。

## 15. 期望结果

使用 GovernSpec 后，你应该得到：

- 一份结构化、可审查、可复用的 AI 任务契约。
- 多个下游工具可直接读取的目标 artifact。
- 明确的权限边界和人工确认规则。
- 可在本地或 CI 运行的输出验收测试。
- 从旧 prompt/rules 迁移到 contract 的路径。
- 对目标平台能力边界的可见性。

最重要的是，团队可以把 AI 任务治理从“散落在 prompt 里的文字”变成“进入工程流程的契约文件”。
