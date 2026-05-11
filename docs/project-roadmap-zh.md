# GovernSpec 项目总规划与当前进度

更新时间：2026-04-25
文档性质：项目总路线图，面向开发、开源发布、文档建设、benchmark、论文和长期维护
当前总进度估计：**82%**

## 1. 进度口径

这里的百分比不是精确工时，而是“可交付成熟度”。它综合考虑代码完成度、测试覆盖、文档完整度、开源包清洁度、benchmark 可复现性、论文材料成熟度、发布流程和长期维护准备。

当前项目已经不处在原型阶段，而是处在**开源发布前后的 release hardening 阶段**。核心功能和测试已经基本完成，开源包已经整理过，中文文档已经补齐一版。还没有达到 100%，主要原因是 GitHub 公开仓库、CI、正式 release、TestPyPI/PyPI、公开 issue 反馈、长期维护节奏和 JOSS 投稿条件还没有完全闭环。

## 2. 当前状态快照

### 2.1 主开发仓库

主开发仓库路径：

```text
D:\GovernSpec
```

当前主仓库状态：

- 已有核心代码、测试、benchmark、论文材料和 release hardening 改动。
- 主仓库存在未提交改动，说明开发工作已经完成了很多，但还需要一次正式整理提交。
- 主仓库中包含论文、benchmark 和 JOSS 准备文件。
- 需要在真正发布前确认主仓库和开源发布包之间的差异，避免两边状态不一致。

### 2.2 开源发布包

开源发布包路径：

```text
D:\GovernSpec\GovernSpec_0.1
```

当前开源发布包状态：

- 已整理为面向 GitHub 上传的目录。
- 已包含英文核心文档、中文核心文档、benchmark、tests、examples、JOSS 准备文件。
- 已新增 `docs/zh/` 中文文档目录。
- 当前中文核心文档数量为 24 份。
- 上传 GitHub 前需要再次清理缓存目录，并重新运行验证命令。

### 2.3 论文与研究材料

当前论文材料状态：

- 已有 ICSE demo 方向草稿。
- 已有 preprint 单栏版本方向材料。
- JOSS 未来投稿材料保留在本地私有工作区，不进入公开仓库。
- 已有本地 artifact-level benchmark 和实验结果。
- 已隔离人工标注相关私有材料，不应进入公开发布包。
- JOSS 当前不建议马上投稿，建议先开源运行一段时间，积累公开开发历史、release、用户反馈和 issue 记录。

## 3. 总体进度评分

| 模块 | 当前成熟度 | 说明 |
|---|---:|---|
| 项目方向与边界 | 95% | 已明确为本地优先的 AI task contract 工具链，不做真实外部 agent 调用。 |
| 核心 schema 与模型 | 90% | `.govern.yaml`、Pydantic 模型、imports、output、tests 等结构已基本稳定。 |
| CLI 与 Python API | 88% | draft、inspect、compile、test、import 等核心路径已可用。 |
| Compile targets | 85% | 已覆盖多个 representative targets，仍需长期根据平台变化维护。 |
| Reverse import | 78% | 已可用，但启发式导入天然需要人工审查和更多样本。 |
| Offline testing | 88% | 断言体系已成型，安全边界和回归测试已经加强。 |
| MCP 集成 | 78% | 已有轻量 MCP server，但发布前仍建议再做一次安全复查。 |
| 测试与质量门禁 | 86% | `pytest` 已通过，仍需补 GitHub Actions 和发布前自动验证。 |
| Benchmark | 80% | 本地可复现实验已具备，真实外部 agent 实验暂不纳入当前开源版本。 |
| 英文文档 | 88% | README、技术指南、release notes、security、contributing 等已具备。 |
| 中文文档 | 82% | 已新增 24 份中文核心文档，可继续补截图、教程和案例。 |
| 开源包整理 | 86% | `GovernSpec_0.1` 已基本可上传，但需要最后一次清洁验证。 |
| PyPI/TestPyPI 发布 | 40% | 尚未上传，需要 build、twine check、TestPyPI 验证。 |
| GitHub 公开发布 | 65% | 包已准备好，但还需要创建仓库、上传、CI、tag 和 release。 |
| JOSS 投稿准备 | 45% | 私有草稿已有基础，但缺公开开发历史、用户反馈和稳定 release 周期。 |

综合判断：**当前总进度约 82%**。如果目标只是“把项目公开到 GitHub”，当前接近 85% 到 90%。如果目标是“达到 JOSS 稳妥投稿”，当前约 45% 到 55%。

## 4. 从 0% 到 100% 的完整路线图

### 0% 到 5%：问题定义与项目动机

目标：

- 明确项目为什么存在。
- 识别 AI agent 工作流中的痛点。
- 定义最小可行场景。

关键问题：

- 团队为什么不能只使用普通 prompt？
- 为什么需要 contract？
- 为什么要本地优先？
- 为什么不直接绑定某一个 agent 平台？

应交付内容：

- 项目一句话定位。
- 目标用户画像。
- 非目标清单。
- 典型使用场景。

验收标准：

- 能用 3 到 5 句话向新用户解释 GovernSpec。
- 能清楚说明它不是 LLM 框架，也不是 agent runtime。
- 能解释它与 prompt template、rules file、structured output schema 的关系。

当前状态：

- 已完成。
- README、技术指南和论文材料中都已经形成稳定叙事。

### 5% 到 10%：系统边界与设计原则

目标：

- 固定项目边界，避免功能失控。
- 明确安全边界。
- 明确开发原则。

设计原则：

- Local-first。
- Deterministic。
- No real LLM API calls。
- No real outbound network workflows in tests。
- Contract before artifact。
- Compile and validate, not runtime enforcement。

应交付内容：

- 安全边界文档。
- 贡献指南。
- agent 协作说明。
- 非目标说明。

验收标准：

- 用户知道哪些事情 GovernSpec 做，哪些事情不做。
- 开发者知道不能引入真实 API key、真实外部调用和高风险自动动作。
- 测试可以在离线环境运行。

当前状态：

- 基本完成。
- `SECURITY.md`、`CONTRIBUTING.md`、`AGENTS.md` 和中文文档已经覆盖。
- 发布前仍建议做一次安全 review。

### 10% 到 20%：Contract schema 与核心数据模型

目标：

- 定义 `.govern.yaml` 的核心结构。
- 建立模型校验。
- 让 contract 能描述任务目标、权限、约束、人工确认、输出和测试。

核心字段：

- `goal`
- `permissions`
- `constraints`
- `human_gates`
- `output`
- `tests`
- `imports`
- `metadata`

应交付内容：

- Pydantic v2 models。
- YAML loader。
- JSON schema 导出。
- 示例 contract。
- schema 相关测试。

验收标准：

- 合法 contract 可以稳定加载。
- 非法字段和错误类型能给出清晰错误。
- schema 与 examples 保持一致。
- 修改模型字段时测试能捕捉回归。

当前状态：

- 基本完成。
- 后续主要是小版本兼容和字段演进。

### 20% 到 30%：IIR 中间表示

目标：

- 把 contract 转为稳定的 Intent Intermediate Representation。
- 为多 target 编译和风险分析提供统一输入。

应交付内容：

- IIR builder。
- imports resolved 后的规范化结构。
- risk signals。
- target capability notes。
- `governspec inspect` 支持。

验收标准：

- 同一 contract 的 IIR 输出稳定。
- imports 合并后的结果可解释。
- 编译器不需要重复解析原始 YAML。
- capability notes 可以说明 target 表达能力不足的地方。

当前状态：

- 已完成主要结构。
- 仍可继续增强 inspect 输出的可读性。

### 30% 到 40%：Compile targets

目标：

- 把同一个 contract 编译到多个 agent 或 structured output target。
- 验证 GovernSpec 的跨平台价值。

当前 target：

- `agents-md`
- `claude-md`
- `cursor-rules`
- `antigravity-rules`
- `skill`
- `openai-structured`
- `gemini-structured`
- `mcp-plan`

应交付内容：

- target compiler。
- 每个 target 的输出测试。
- capability notes。
- examples。
- 文档说明。

验收标准：

- 同一 contract 可以生成多个 target artifact。
- Markdown target 可读。
- structured target 可被 schema 工具检查。
- target 不支持的语义会被记录，而不是静默丢失。

当前状态：

- 已完成主要能力。
- 后续维护重点是平台格式变化、更多 examples 和用户反馈。

### 40% 到 50%：Reverse import

目标：

- 从已有 artifact 中恢复 contract 草稿。
- 降低迁移门槛。

支持来源：

- `AGENTS.md`
- Claude 风格 Markdown。
- Cursor Rules。
- OpenAI structured output。
- Gemini structured output。

应交付内容：

- importer modules。
- 共享解析 helper。
- round-trip tests。
- 文档说明。

验收标准：

- 常见 artifact 可以导回 contract 草稿。
- 导入结果不会被包装成完美恢复，而是明确需要人工审查。
- round-trip benchmark 能量化字段保真度。

当前状态：

- 可用，但仍属于需要长期改进的启发式模块。
- 更大规模样本会提高可信度。

### 50% 到 60%：Offline acceptance testing

目标：

- 在不调用真实 LLM 的情况下验证输出是否满足 contract。
- 把自然语言要求转成可运行的 acceptance checks。

断言类型：

- `contains`
- `not_contains`
- `regex`
- `no_regex`
- `required_sections`
- `max_words`
- `max_chars`
- `json_schema`
- `language`
- `references`

应交付内容：

- `test_output` API。
- CLI `governspec test`。
- 正常输出样本。
- 缺陷输出样本。
- 每类断言的测试。

验收标准：

- valid outputs 应通过。
- targeted defect outputs 应失败。
- 断言结果可解释。
- 正则风险有边界处理。

当前状态：

- 已完成主要能力。
- 后续可以增强错误报告、差异展示和更多断言类型。

### 60% 到 70%：MCP 与集成表面

目标：

- 让 MCP client 能使用 GovernSpec 的本地能力。
- 保持 MCP server 薄而安全。

应交付内容：

- MCP server。
- `governspec.compile`。
- `governspec.test`。
- 受控 resource 访问。
- 安全边界测试。

验收标准：

- MCP 不应成为任意本地文件读取接口。
- caller-supplied path 必须受控。
- 错误信息不能泄漏不必要的本地信息。
- 不引入真实外部 API 调用。

当前状态：

- 已有 MCP 能力。
- 发布前建议再做一次 focused security review。

### 70% 到 80%：Benchmark、论文实验与可复现数据

目标：

- 建立可复现实验包。
- 支撑 ICSE demo、preprint 和后续 JOSS 叙事。

应交付内容：

- 本地研究 benchmark artifact。
- contracts。
- valid outputs。
- defect outputs。
- handwritten artifacts。
- labels。
- experiment scripts。
- generated results。
- tables and numbers。

核心结果文件：

- `compile_matrix.json`
- `roundtrip_fidelity.json`
- `assertion_eval.json`
- `summary.json`
- `tables.md`
- `numbers.md`

验收标准：

- `run_all.py` 可以一键生成结果。
- 每个结果文件 schema 稳定。
- 论文中的数字来自生成文件。
- 私有标注材料不进入公开发布包。

当前状态：

- 已完成可用版本。
- 后续如果要投更强论文，需要真实用户数据、更大规模 benchmark 或外部 agent 实验。

### 80% 到 85%：英文文档与开源基础设施

目标：

- 让陌生用户能安装、运行、理解和贡献。
- 让开源仓库满足基本社区预期。

应交付内容：

- `README.md`
- `docs/technical-guide.md`
- `docs/integrations.md`
- `docs/iir.md`
- `docs/migration-v0.1.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `LICENSE`
- `CITATION.cff`
- release notes。

验收标准：

- README 能让新用户 10 分钟内跑通最小例子。
- 安装、测试、CLI、benchmark 都有说明。
- 安全报告和贡献方式清楚。
- 许可证和引用信息齐备。

当前状态：

- 基本完成。
- 当前处于这一区间的后半段。

### 85% 到 88%：中文文档与可访问性

目标：

- 让中文用户也能顺畅理解和使用项目。
- 降低使用门槛。

应交付内容：

- `docs/zh/README.md`
- 中文技术指南。
- 中文贡献、安全、发布、benchmark、论文读者版。
- 中文文档入口。

验收标准：

- 中文用户能从 `docs/zh/README.md` 找到核心说明。
- 命令、路径、字段名保持英文原样。
- 中文文档不改变代码语义。
- 英文文档仍保留为正式开源主文档。

当前状态：

- 已完成第一版。
- 当前中文文档数量为 24 份。
- 后续可以补截图、教程、FAQ 和常见错误排查。

### 88% 到 92%：GitHub 首次公开发布

目标：

- 把项目从本地开发状态转为公开开源项目。

应交付内容：

- 新 GitHub public repository。
- 初始 commit。
- `v0.1.0` tag。
- GitHub release。
- GitHub Issues。
- README badges。
- GitHub Actions CI。

验收标准：

- 新用户可以从 GitHub clone 并运行测试。
- CI 在 pull request 上自动运行。
- release 页面说明清晰。
- repository 不包含私有标注材料、缓存、构建产物或本地路径泄漏。

当前状态：

- 尚未完成。
- 开源包已经接近可上传。
- 这是下一阶段最重要的动作。

### 92% 到 95%：TestPyPI/PyPI 发布

目标：

- 让用户可以通过 package manager 安装。
- 验证包元数据和安装体验。

应交付内容：

- build artifacts。
- `twine check` 通过。
- TestPyPI 上传。
- TestPyPI 安装验证。
- 正式 PyPI 发布。

推荐命令：

```bash
python -m build
twine check dist/*
twine upload --repository testpypi dist/*
```

正式发布前再执行：

```bash
twine upload dist/*
```

验收标准：

- `pip install governspec` 可以安装正式包。
- 安装后 `governspec --help` 可运行。
- 包内 examples、schema 和 resources 被正确包含。
- PyPI 版本号不可覆盖，发布前必须确认版本。

当前状态：

- 尚未完成。
- 建议先 TestPyPI，再正式 PyPI。

### 95% 到 98%：公开维护、用户反馈与稳定化

目标：

- 让项目经过真实开源使用检验。
- 积累公开开发历史。

应交付内容：

- Issues triage。
- bug fix releases。
- 用户反馈记录。
- FAQ。
- 更多 examples。
- 公开 roadmap。
- compatibility notes。

验收标准：

- 至少经历若干周到数月的公开维护。
- 有稳定 release 节奏。
- 常见安装和使用问题被文档吸收。
- 重要 bug 有回归测试。

当前状态：

- 尚未开始。
- 这是 JOSS 之前最关键的非代码阶段。

### 98% 到 100%：JOSS 或其他正式投稿

目标：

- 在项目已经公开、可安装、可复现、有人可审的基础上提交软件论文。

应交付内容：

- JOSS 投稿草稿。
- 参考文献核查。
- 软件 archive 或 release DOI。
- 完整 installation instructions。
- Example usage。
- Tests。
- Community guidelines。
- Statement of need。
- Public repository history。

验收标准：

- JOSS reviewer 可以从零安装、运行、测试和理解软件。
- 论文与仓库状态一致。
- 引用真实可查。
- 仓库显示持续公开开发，而不是临时一次性上传。

当前状态：

- 论文准备已有基础。
- 不建议马上投稿。
- 建议开源后维护约 6 个月，再根据公开反馈更新 JOSS 投稿材料。

## 5. 当前阶段定位

当前项目处在：

```text
82%：release hardening and public launch preparation
```

这意味着：

- 不是想法阶段。
- 不是简单 prototype。
- 核心实现已经接近可公开。
- 文档和 benchmark 已经有实质内容。
- 最大缺口不再是“能不能跑”，而是“能不能稳定公开发布、让陌生用户顺利使用、让论文评审相信项目成熟”。

## 6. 当前最该做的 10 件事

### 1. 冻结开源包目录

目标路径：

```text
D:\GovernSpec\GovernSpec_0.1
```

要做：

- 清理 cache。
- 清理 build artifacts。
- 确认没有私有标注材料。
- 确认中文文档和英文文档都在。

完成标准：

- 没有 `.git/`、`.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/`、`__pycache__/`、`build/`、`dist/`、`output/`。

### 2. 跑发布前验证

推荐命令：

```bash
pytest -q
ruff check .
mypy
python benchmark/run_benchmark.py
```

完成标准：

- 所有命令通过。
- benchmark 结果文件重新生成。
- README 中的命令仍然可用。

### 3. 核对主仓库和开源包差异

要做：

- 明确哪些改动只在主仓库。
- 明确哪些改动只在 `GovernSpec_0.1`。
- 决定开源后以哪个目录作为 canonical source。

推荐策略：

- 直接将 `GovernSpec_0.1` 作为 GitHub 初始上传内容。
- 后续把 GitHub 仓库作为新的唯一主线。

### 4. 创建 GitHub 仓库

要做：

- 创建 public repository。
- 上传开源包。
- 创建初始 commit。
- 打 `v0.1.0` tag。
- 打开 Issues。

完成标准：

- 外部用户可以 clone。
- README 页面显示正常。
- LICENSE、SECURITY、CONTRIBUTING 可见。

### 5. 配置 GitHub Actions

建议 CI 包含：

- install。
- pytest。
- ruff。
- mypy。
- benchmark smoke test。

完成标准：

- 每次 push 和 PR 自动运行。
- README 可以添加 CI badge。

### 6. 做 TestPyPI 验证

要做：

- build package。
- `twine check`。
- 上传 TestPyPI。
- 新环境安装测试。

完成标准：

- `governspec --help` 可运行。
- 包内 resources 正确可用。

### 7. 决定是否正式 PyPI

建议：

- GitHub release 稳定后再正式 PyPI。
- 不要抢发不确定版本号。

完成标准：

- `pip install governspec` 可用。
- release notes 与 PyPI 描述一致。

### 8. 增强用户教程

优先补：

- 5 分钟快速开始。
- 从 prompt 到 contract 的教程。
- 从 contract 到 `AGENTS.md` 的教程。
- 从 output 到 `governspec test` 的教程。
- 常见错误排查。

完成标准：

- 非作者用户可以独立跑通完整流程。

### 9. 开始公开维护周期

要做：

- 收集 issue。
- 记录 bug。
- 补回归测试。
- 发布 patch versions。

完成标准：

- 形成公开开发历史。
- 有真实用户反馈或至少外部 reviewer 反馈。

### 10. 六个月后更新 JOSS 投稿材料

要做：

- 更新 statement of need。
- 更新 examples。
- 更新安装方式。
- 更新 benchmark 结果。
- 核查参考文献。
- 确认 JOSS 要求。

完成标准：

- JOSS 投稿材料与公开仓库完全一致。
- repo 有足够公开历史。

## 7. 风险清单

### 风险 1：主仓库和开源包不同步

影响：

- 可能导致开源版本缺少最新修复。
- 可能导致主仓库中还有私有或不适合公开的材料。

缓解：

- 明确以 `GovernSpec_0.1` 作为当前发布包。
- 上传前生成一次 manifest。
- 开源后把 GitHub 仓库作为新的 canonical source。

### 风险 2：发布包夹带缓存或私有材料

影响：

- 影响专业度。
- 可能泄漏本地路径或私有研究材料。

缓解：

- 上传前运行 cache scan。
- 检查 annotation 相关文件不在公开包。
- 检查 `.gitignore` 和 manifest。

### 风险 3：用户不知道怎么开始

影响：

- 项目看起来有门槛。
- 真实 adoption 降低。

缓解：

- 强化 README 快速开始。
- 中文文档提供完整入门路径。
- 增加 tutorial 和 FAQ。

### 风险 4：JOSS 投稿过早

影响：

- 可能因为公开开发历史不足、用户证据不足或软件成熟度不足被质疑。

缓解：

- 先开源。
- 积累 3 到 6 个月公开维护历史。
- 有 release、issue、CI 和用户反馈后再投。

### 风险 5：外部 agent 平台格式变化

影响：

- target 输出可能需要维护。

缓解：

- 保持 target compiler 小而集中。
- 用 capability notes 记录表达限制。
- 给每个 target 增加 fixtures 和 regression tests。

## 8. 未来版本规划

### v0.1.0

目标：

- 首次公开开源。
- 固定基本 contract schema。
- 提供 CLI、core、MCP、examples、benchmark 和文档。

必须完成：

- GitHub public repo。
- CI。
- release tag。
- release notes。
- 清洁发布包。

### v0.1.1

目标：

- 修复首次公开反馈。
- 改善安装和文档。

可能内容：

- README FAQ。
- 更多 examples。
- CLI 错误信息优化。
- benchmark smoke test 优化。

### v0.2.0

目标：

- 增强 reverse import 和 target fidelity。
- 稳定更多真实使用场景。

可能内容：

- 更严格的 schema compatibility rules。
- 更多 import source tests。
- 更好的 diff report。
- 更清晰的 target capability model。

### v0.3.0

目标：

- 进入论文投稿前稳定阶段。

可能内容：

- 更完整用户教程。
- 更多 benchmark cases。
- 可选 external-agent experiment harness，但不默认调用真实 API。
- JOSS 投稿材料更新。

## 9. 100% 完成的定义

项目达到 100% 不代表永远不用维护，而是代表当前阶段的“开源加论文准备闭环”完成。

100% 标准：

- GitHub public repo 已上线。
- `v0.1.0` release 已发布。
- CI 运行稳定。
- README、英文文档和中文文档完整。
- TestPyPI 已验证，正式 PyPI 已发布或明确决定暂缓。
- benchmark 可复现。
- 私有材料已隔离。
- 有至少一个 patch release 或公开 issue 处理记录。
- JOSS 投稿材料与仓库一致。
- 引用文献核查完成。
- 可以有信心邀请外部用户和 reviewer 使用。

## 10. 给项目负责人的判断

如果你的目标是“马上开源”，现在已经接近可执行。最关键的是做最后一次清洁验证，然后上传 `D:\GovernSpec\GovernSpec_0.1`。

如果你的目标是“马上投 JOSS”，现在还不建议。不是因为项目弱，而是因为 JOSS 更看重软件已经公开、可安装、有人能复现、有维护历史。先开源，跑一段时间，半年后投会更稳。

如果你的目标是“把 GovernSpec 做成长期项目”，下一步最重要的不是继续疯狂加功能，而是稳定发布、收集反馈、补教程、补 CI、做小版本迭代。这个项目已经从“能不能做”走到了“怎么让更多人放心用”的阶段。
