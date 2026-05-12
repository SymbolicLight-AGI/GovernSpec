# `*.govern.yaml` 新手教程

这份教程面向第一次使用 GovernSpec 的用户。读完后，你应该能写出一份可验证、可编译的 `*.govern.yaml`，并把它转换成 `AGENTS.md`、通用 prompt、structured output payload 或 MCP plan。

GovernSpec 的核心思路很简单：

```text
*.govern.yaml     = AI 任务合同
governspec validate = 检查合同是否合法
governspec inspect  = 查看最终归一化规则
governspec compile  = 编译成目标工具能读的格式
governspec test     = 检查输出是否满足合同
```

它不会调用真实 LLM API，也不需要 API key。它负责管理任务规则，不负责替代 agent runtime。

## 1. 什么时候需要 `*.govern.yaml`

当你希望一个 AI 任务具备明确边界时，就适合写 `*.govern.yaml`：

- 代码审查：只读仓库，不允许直接修改文件。
- 客户简报：允许读取材料，但不能泄露隐私。
- 合同初审：必须标注不确定性，不能给出最终法律意见。
- 质量检查：输出必须包含固定章节和风险等级。
- JSON 报告：输出必须满足指定 JSON schema。

如果只是一次随手提问，直接写 prompt 就够了。如果这个任务要复用、要进 Git、要经过 review，或要编译到多个 AI 工具，就适合用 GovernSpec。

## 2. 最推荐的生成方式

新手不需要从零手写 YAML。推荐先用自然语言生成草稿：

```bash
governspec draft "帮我审查这个仓库的代码变更，只读文件，不允许修改代码，不允许联网，输出总体结论、必须修复、建议和测试建议" --out examples/my_review.govern.yaml
```

然后验证：

```bash
governspec validate examples/my_review.govern.yaml
```

再查看归一化后的规则：

```bash
governspec inspect examples/my_review.govern.yaml
```

`draft` 是本地启发式生成，不调用 LLM。它适合起草，但生成后仍然需要人工确认权限、约束和输出要求。

## 3. 另一种方式：生成空模板

如果你想从模板开始：

```bash
governspec init --file examples/my_task.govern.yaml --locale zh-CN
```

生成后重点修改这些字段：

- `metadata.name`
- `task.goal`
- `inputs`
- `permissions`
- `constraints`
- `output`
- `tests`

## 4. 完整示例

下面是一份完整的代码审查合同。你可以复制后改成自己的任务。

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

## 5. 每个字段负责什么

| 字段 | 作用 | 常见写法 |
| --- | --- | --- |
| `version` | GovernSpec schema 版本 | 当前使用 `"0.1"` |
| `kind` | 文档类型 | 单个任务用 `"GovernSpec"` |
| `metadata` | 名称、标题、描述、负责人 | 用于识别和审查 |
| `task` | 任务目标、读者和优先级 | 把“要做什么”写清楚 |
| `context` | 背景、事实、假设、术语表 | 信息不足时写入 assumptions |
| `inputs` | 输入材料 | 可以是目录、文件、文档或 JSON |
| `permissions` | 权限边界 | 明确能不能联网、读写文件、调用工具 |
| `constraints` | 硬约束 | 禁止事项和必须遵守的规则 |
| `evidence` | 证据要求 | 是否需要来源、是否标注不确定性 |
| `output` | 输出格式 | `markdown`、`text` 或 `json` |
| `quality` | 风格和内容偏好 | 语气、必须包含、必须避免 |
| `human_gates` | 人工确认门 | 高风险动作前要求确认 |
| `tests` | 离线验收规则 | 检查章节、长度、JSON schema 等 |

最重要的是这五块：

```text
task        = 要做什么
permissions = 能做什么，不能做什么
constraints = 执行时必须遵守什么
output      = 最终结果长什么样
tests       = 怎么检查结果合不合格
```

## 6. 编译成 `AGENTS.md`

验证通过后，可以编译成 `AGENTS.md` 风格的文件：

```bash
governspec compile examples/my_review.govern.yaml --target agents-md --out examples/my_review.agents.md
```

如果不传 `--out`，结果会直接打印到终端：

```bash
governspec compile examples/my_review.govern.yaml --target agents-md
```

常见 target：

| Target | 输出用途 |
| --- | --- |
| `agents-md` | 生成 `AGENTS.md` 风格指令 |
| `prompt` | 生成通用 Markdown prompt |
| `openai-structured` | 生成 OpenAI Structured Outputs payload |
| `gemini-structured` | 生成 Gemini structured output payload |
| `mcp-plan` | 生成 MCP 执行计划摘要 |
| `skill` | 生成通用 skill bundle |

## 7. 检查输出是否合格

假设 agent 的输出保存在 `output.md`：

```bash
governspec test examples/my_review.govern.yaml --output output.md
```

它会按 `tests` 里的断言检查输出。例如：

- `required_sections`：要求输出包含 `output.sections` 中的所有章节。
- `not_contains`：要求输出不能包含某段文本。
- `contains`：要求输出必须包含某段文本。
- `max_words`：要求输出不超过 `output.max_words`。
- `json_schema`：要求 JSON 输出符合 schema。

这些测试是确定性的格式和规则检查，不会判断复杂事实是否真实。高风险任务仍然需要人工 review。

## 8. 如果要输出 JSON

Markdown 输出使用 `sections`，JSON 输出使用 `schema`：

```yaml
output:
  format: "json"
  language: "zh-CN"
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

然后可以编译成 OpenAI Structured Outputs：

```bash
governspec compile report.govern.yaml --target openai-structured --out report.openai-structured.json
```

## 9. 如何迁移到其他行业

这套模板结构通用，但内容必须行业化。迁移时优先改这些字段：

| 行业 | 应重点修改 |
| --- | --- |
| 软件工程 | `inputs`、`permissions.filesystem`、`constraints`、测试章节 |
| 制造业 | `context.domain`、质量标准、异常等级、人工确认门 |
| 法务 | 免责声明、证据要求、不可替代律师意见的约束 |
| 金融 | 数据来源、风险提示、禁止投资建议的边界 |
| 医疗 | 隐私限制、非诊断声明、人工确认规则 |
| 销售 | 客户资料隐私、输出结构、跟进建议边界 |

不要指望 GovernSpec 自动懂行业规则。你需要把行业内不能越界的规则写进 `constraints`、`evidence` 和 `human_gates`。

## 10. 提交前检查清单

提交 `*.govern.yaml` 前建议确认：

- `governspec validate <file>` 通过。
- `governspec inspect <file>` 显示的权限和约束符合预期。
- `permissions` 没有无意放开联网、写文件、删文件或采购等高风险能力。
- `constraints` 写清楚禁止事项。
- `output.sections` 是真实需要的章节，不是装饰性标题。
- `tests` 至少覆盖必须章节、禁止文本或 JSON schema。
- 高风险任务包含 `human_gates`。
- 生成的下游文件来自 `compile`，不要长期手工维护编译产物。

## 11. 常见错误

### 字段名写错

GovernSpec 不接受未知字段。比如 `outputs` 不是合法字段，应该写 `output`。

### 忘记写 `max_words`

`markdown` 和 `text` 输出需要 `max_words`。如果不想限制太死，可以给一个较大的值。

### JSON 输出写成 `json_schema`

YAML 里应写：

```yaml
output:
  format: "json"
  schema:
    type: "object"
```

不要写成：

```yaml
output:
  format: "json"
  json_schema:
    type: "object"
```

### 只写目标，不写权限

`task.goal` 说明做什么，`permissions` 说明能做什么。两者都需要。

### 把测试当成事实验证

`governspec test` 能检查格式、章节、长度、文本和 JSON 结构，但不能证明输出内容在事实层面一定正确。

## 12. 推荐工作流

日常使用可以按这个顺序：

```bash
governspec draft "用自然语言描述你的任务" --out task.govern.yaml
governspec validate task.govern.yaml
governspec inspect task.govern.yaml
governspec compile task.govern.yaml --target agents-md --out task.agents.md
governspec test task.govern.yaml --output output.md
```

如果你已经有模板：

```bash
governspec init --file task.govern.yaml --locale zh-CN
```

如果你已经有 `AGENTS.md`：

```bash
governspec import AGENTS.md --out imported.govern.yaml
governspec validate imported.govern.yaml
governspec inspect imported.govern.yaml
```

最稳妥的原则是：先维护 `*.govern.yaml`，再编译成其他工具需要的文件。这样规则有源头，变更也更容易 review。
