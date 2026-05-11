# GovernSpec 仓库文件地图

本文档记录当前仓库中需要长期维护的正式文件与目录。它只说明文件在哪里、负责什么、修改时会影响什么，不替代需求文档或详细设计文档。

## 根目录

- `pyproject.toml`：Python 包元数据、依赖、CLI 入口、pytest、ruff、mypy 配置。修改依赖、版本号、包发现规则或质量门禁时会影响安装、测试和发布。
- `README.md`：英文项目主入口文档，说明定位、安装、快速开始、target、benchmark 和开发命令。修改 CLI 行为、target、示例或发布流程时应同步更新。
- `README.zh-CN.md`：中文 README。修改根目录英文 README 的关键信息时，应同步审查中文版本是否需要更新。
- `AGENTS.md`：项目级 agent 协作规则。修改项目约束、命令或维护规则时应同步审查。
- `MANIFEST.in`：源码包文件包含规则。修改 examples、schema、文档或包数据时会影响发布包内容。
- `.gitattributes`：文本文件换行与编码相关规则。修改后会影响 Git 工作区换行处理。
- `.gitignore`：忽略缓存、构建产物、临时发布包和本地私有目录。新增运行产物目录时应同步更新。

## Python 包

- `packages/governspec-core/src/governspec_core/spec/`：GovernSpec 与 GovernPack 的 Pydantic 模型、YAML 解析和 schema 入口。修改字段会影响 schema、examples、compiler、importer、tests 和文档。
- `packages/governspec-core/src/governspec_core/imports/`：`imports` 解析与保守合并规则。修改权限、测试、约束合并逻辑时会影响 `inspect`、`compile` 和 `test` 的最终语义。
- `packages/governspec-core/src/governspec_core/iir/`：归一化 IIR 构建与风险信号。修改 IIR 字段会影响 target compiler、MCP plan、inspect 输出和 benchmark。
- `packages/governspec-core/src/governspec_core/targets/`：多目标编译器，包括 `agents-md`、`claude-md`、`cursor-rules`、`openai-structured`、`gemini-structured`、`mcp-plan` 和 `skill`。新增 target 或调整输出格式时应更新 tests、README 和 integrations 文档。
- `packages/governspec-core/src/governspec_core/importers/`：从 AGENTS.md、CLAUDE.md、Cursor Rules、OpenAI/Gemini structured output 反向导入 draft contract。修改启发式导入时应补 round-trip 测试。
- `packages/governspec-core/src/governspec_core/testing/`：离线验收断言执行器。新增 assertion 类型时应更新 README、测试和 benchmark 缺陷样本。
- `packages/governspec-core/src/governspec_core/draft.py`：本地启发式 draft generator。修改中文或英文规则推断时应运行 `tests/test_draft.py`。
- `packages/governspec-cli/src/governspec/cli.py`：Typer CLI，包括 `validate`、`inspect`、`compile`、`test`、`init`、`schema`、`doctor`、`examples`、`workflow`、`draft` 和 `import`。修改命令参数时应更新 CLI 测试和文档。
- `packages/governspec-mcp/src/governspec_mcp/server.py`：薄 MCP server，暴露 validate、inspect、compile、test 工具和资源。修改路径解析或工具返回值时应更新 MCP 测试。

## TypeScript 与编辑器集成

- `packages/governspec-ts/`：TypeScript CLI wrapper。修改 CLI 参数或 JSON 输出约定时需要检查该 wrapper。
- `packages/governspec-vscode/`：VS Code extension MVP。修改 CLI 命令、target 列表或 MCP setup 建议时需要同步检查。

## 示例、schema 与测试

- `examples/`：用户可复制的 contract、pack 和输出样例。修改 schema 字段、默认模板、target 行为或测试断言时应同步样例。
- `schema/governspec.schema.json`：导出的 JSON Schema。修改模型字段后应重新生成并检查。
- `tests/`：pytest 测试套件，覆盖 parser、validator、compiler、CLI、draft、importer、MCP、benchmark 等路径。行为变更应优先补最小相关测试。

## Benchmark 与公开文档

- `benchmark/`：离线 benchmark、reproducibility benchmark、contracts、outputs、results 和脚本。修改 compiler、importer、tester 或指标时应同步结果和测试。
- `benchmark.md`：benchmark 使用说明和记录模板。
- `failure-cases.md`：真实失败案例记录模板。

## 文档与发布

- `docs/technical-guide.md`：技术指南，解释核心概念、流程和边界。
- `docs/integrations.md`：集成说明，记录 target、reverse import、MCP 和 VS Code 策略。
- `docs/iir.md`：IIR 设计说明。
- `docs/migration-v0.1.md`：v0.1 schema 迁移说明。
- `docs/release-checklist.md`：发布前验证清单。
- `docs/project-roadmap-zh.md`：中文项目路线图和进度口径。
- `CONTRIBUTING.md`、`SECURITY.md`、`CODE_OF_CONDUCT.md`、`CITATION.cff`：开源治理、披露、安全和引用材料。

## 不记录的运行产物

以下目录或文件属于缓存、构建产物、临时验证结果或本地私有材料，不应写入本文件的正式维护清单：`node_modules/`、`.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/`、`dist/`、`build/`、`output/`、`.tmp_*`、本地虚拟环境、临时截图和日志。
