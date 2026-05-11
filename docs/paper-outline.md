# GovernSpec 投稿大纲（双版本）

更新时间：2026-04-24  
状态：已根据公开官方页面和仓库现状校正关键事实，可作为后续写作母版。

---

## 0. 事实基线

### 0.1 仓库现状，写作时必须保持一致

- `GovernSpec` 当前是一个 `local-first`、`zero-intrusion` 的契约编译器。
- 当前仓库中有 `10` 个 compile targets：
  - `agents-md`
  - `antigravity-rules`
  - `claude-md`
  - `cursor-rules`
  - `gemini-structured`
  - `mcp-plan`
  - `openai-json`
  - `openai-structured`
  - `prompt`
  - `skill`
- 当前仓库中有 `5` 个 import source types：
  - `agents-md`
  - `claude-md`
  - `cursor-rules`
  - `openai-structured`
  - `gemini-structured`
- 当前仓库中有 `10` 种确定性离线断言：
  - `required_sections`
  - `contains`
  - `not_contains`
  - `regex`
  - `no_regex`
  - `max_words`
  - `max_chars`
  - `json_schema`
  - `json_path_exists`
  - `json_array_min_items`

### 0.2 论文里建议坚持的边界

- 核心问题：如何在**不修改 agent runtime**的前提下，把一份统一契约传播到多个异构 agent 入口，并对最终产出执行确定性离线验收。
- 核心能力：`single-source contract authoring`、`multi-target compilation`、`reverse import`、`deterministic offline acceptance testing`。
- 非目标：
  - 不宣称 fail-closed runtime enforcement。
  - 不宣称替代 tool-call firewall、reference monitor、policy engine。
  - 不宣称检测语义真实性、推理正确性或事实真伪。

### 0.3 写作时建议统一使用的主张句

> GovernSpec provides a local-first, zero-intrusion governance layer that compiles a single contract into agent-native artifacts and pairs them with deterministic offline acceptance tests.

上面这句话比 `enforce behavioral constraints` 更稳，更符合系统实际边界。

### 0.4 已核验的投稿信息

- `ICSE 2027 Tool Demonstration and Data Showcase`
  - 官方页面已公开
  - 截稿时间：`2026-10-23 (AoE)`
  - 篇幅：`4 pages`, `inclusive of all references, figures, tables, appendices`
  - 格式：`IEEE conference proceedings format`
  - 需要可访问工具链接和 `3-5` 分钟演示视频
- `FSE 2027 Research Track`
  - 官方页面已公开
  - 截稿时间：`2026-10-02 (AoE)`
  - 篇幅：`18 pages + 4 pages references`
  - 格式：`single-column ACM acmsmall`
- `FSE 2027 Industry Track`
  - 截至 `2026-04-24`，我未检到公开 CFP
  - 因此本文件中的“FSE 长文版”先按**长篇研究论文叙事**组织，后续若 `Industry Track` 开放，再做裁剪和改 framing

### 0.5 已核验的相关工作对象

这些对象可以进入 related work，但请区分“研究论文”和“生态系统/官方文档”。

- 研究论文
  - `Policy Compiler for Secure Agentic Systems` (`arXiv:2602.16708`)
  - `Agent Behavioral Contracts: Formal Specification and Runtime Enforcement for Reliable Autonomous AI Agents` (`arXiv:2602.22302`)
  - `Mind the GAP: Text Safety Does Not Transfer to Tool-Call Safety in LLM Agents` (`arXiv:2602.16943`)
- 生态系统/官方资料
  - `Microsoft Agent Governance Toolkit` 官方博客与仓库说明
  - `OSSA Specification`

写作注意：

- 不要再把 `arXiv:2602.16943` 写成 `Edictum`。
- 如果要用 `AgentContract` 这个名字，必须先确认你引用的是论文、开源项目还是产品页面，避免把不同来源混成一个对象。

---

## 1. 共同写作原则

### 1.1 标题策略

优先使用 `governance`、`contract compilation`、`heterogeneous agents`、`runtime-free` 或 `zero-intrusion`，避免直接使用 `enforcement`。

更稳的标题候选：

1. `GovernSpec: Zero-Intrusion Contract Compilation for Governing Heterogeneous AI Agents`
2. `Runtime-Free Contract Compilation for Agent Governance across Heterogeneous AI Toolchains`
3. `GovernSpec: Single-Source Contract Compilation and Offline Acceptance Testing for AI Agent Governance`

### 1.2 不建议再用的表述

- `Enforcing Behavioral Constraints Without Runtime Modification`
- `首次证明`
- `填补空白`
- `重要理论贡献`
- `10 种下游工具已原生支持`

更稳的替代写法：

- `governing behavior through agent-native artifacts`
- `to our knowledge`
- `addresses an underexplored combination`
- `introduces a compile-time loss reporting mechanism`
- `10 compile targets implemented in the current prototype`

### 1.3 评估设计的总原则

- 不要把 `GovernSpec` 和 runtime firewall 系统做成“谁更安全”的对打。
- 可以比较**接入方式、部署摩擦、可移植性、表达能力损失**，但要明确 threat model 不同。
- 最公平的主 baseline 其实是：
  - `hand-authored per-platform artifacts`
  - `prompt-only governance without a source contract`
- runtime enforcement 系统更适合放在 discussion 和 qualitative comparison，而不是唯一量化 baseline。

### 1.4 论文里建议明确区分的三个数字

- `10 compile targets`，这是实现规模
- `5 import source types`，这是 round-trip 范围
- `6 representative targets for evaluation` 或 `5 representative targets for evaluation`，这是实验采样设计

不要把这三组数字混写。

---

## 2. ICSE Demo 版

### 2.1 投稿定位

这个版本应该把重点放在：

- 工具是否解决了一个真实、常见、尚未被很好支持的工程问题
- 工作流是否清晰、可复现、可演示
- artifact 是否可访问
- 初步验证是否足以说明“这个工具值得社区使用”

不应该把重点放在：

- 大规模理论证明
- 过强的 novelty claim
- 与 runtime enforcement 系统做安全强度竞赛

### 2.2 推荐标题

首选：

`GovernSpec: Zero-Intrusion Contract Compilation and Offline Acceptance Testing for Heterogeneous AI Agents`

备选：

`GovernSpec: A Local-First Tool for Compiling Agent Governance Contracts into Native Artifacts`

### 2.3 一句话摘要定位

> We present GovernSpec, a local-first tool that lets developers author a single governance contract, compile it into native artifacts used by heterogeneous AI agent platforms, and validate generated outputs with deterministic offline checks, without modifying agent runtimes.

### 2.4 适合 ICSE demo 的核心贡献

建议只写 3 点：

1. 一个可运行的 `single-source contract` 工具链，支持从 `govern.yaml` 到多个 agent-native artifacts 的编译。
2. 一个与编译流程配套的 `reverse import` 和 `offline acceptance testing` 工作流。
3. 一组展示工具可用性与表达边界的轻量级实证结果。

### 2.5 4 页结构建议

#### 1. Introduction（约 0.6 页）

写法目标：

- 用一个跨平台团队场景开头：同一仓库里同时使用 `Codex`、`Claude Code`、`Cursor`、API structured output。
- 指出当前真实痛点不是“没有 policy”，而是“policy 分散在不同 artifact 中，不可统一维护，不可统一验证”。
- 明确本文问题：

> Can a single contract be compiled into native governance artifacts across heterogeneous AI agent toolchains, without modifying their runtimes, while still supporting deterministic post-hoc validation?

结尾给 3 条贡献，保持克制。

#### 2. Tool Overview（约 0.9 页）

只讲端到端工作流，不要把细节铺太满：

```text
govern.yaml
  -> validate
  -> resolve imports
  -> normalize to IIR
  -> compile to target artifacts
  -> run agent
  -> validate output with offline assertions
```

这里放 `Figure 1`，一张总览图就够。

#### 3. Key Design Choices（约 1.0 页）

只保留最能体现“为什么这个工具有工程价值”的三个设计点：

1. `IIR` 作为 source schema 和 target format 之间的隔离层
2. `constraint_loss` 或更稳的命名 `compile-time loss report`
3. `deterministic offline assertions` 作为与 runtime-free 治理相配套的验收层

不要在 demo 版里展开大篇幅形式化定义，可以用简短定义替代：

- contract
- target artifact
- loss report
- acceptance test

#### 4. Demonstration Scenario and Initial Validation（约 1.1 页）

建议围绕一个统一 case 展开：

- 输入：一个 `privacy-sensitive code review` 或 `customer brief generation` 契约
- 编译到：
  - `AGENTS.md`
  - `CLAUDE.md`
  - `.cursor/rules/governspec.mdc`
  - `openai-structured`
  - `mcp-plan`
- 展示：
  - 编译结果
  - 一个 compile-time loss report 示例
  - 从某个 artifact 反向导回契约
  - 对产出执行 `governspec test`

初步验证只做三件事：

1. `multi-target portability`
2. `round-trip feasibility`
3. `defect detection examples`

这三项足够支撑 demo，不必塞 4 个正式 RQ。

#### 5. Availability and Demo Script（约 0.4 页）

明确列出：

- 仓库地址
- 安装命令
- demo 视频结构
- artifact availability

### 2.6 ICSE demo 版建议保留的图表

- `Figure 1`：end-to-end workflow
- `Table 1`：representative targets and what each target can express
- `Figure 2`：one compile-and-test walkthrough

如果版面吃紧，优先保留 `Figure 1` 和 `Table 1`。

### 2.7 ICSE demo 版建议使用的实证包

最小可投稿包：

- `3` 个 representative contracts
- `5` 个 representative targets
- `5` 个 import source types 中至少 `3` 个完成 round-trip 演示
- `8-12` 个 defect samples，用来展示断言能抓住结构性和格式性问题

更稳的版本：

- `6` 个 contracts
- `5` 个 targets
- `5` 个 import source types 全覆盖
- `20-30` 个 defect samples

### 2.8 ICSE demo 版不建议写死的内容

- 不要在 abstract 中提前写 `87%`、`94%` 这种尚未稳定复现实验数字。
- 不要写“首次形式化了编译降级”。
- 不要写“证明了不修改 runtime 也能 enforce 行为约束”。

更稳的替代句式：

- `We observe that native artifacts vary significantly in what governance information they can faithfully encode.`
- `Our prototype reports compile-time information loss when the target artifact cannot faithfully encode part of the source contract.`

### 2.9 ICSE demo 版可直接落文的摘要骨架

第一句：问题背景，异构 agent 平台导致治理规则碎片化。
第二句：已有工作多依赖 runtime interception 或 framework-specific integration。
第三句：本文提出 `GovernSpec`。
第四句：系统能力，`single-source contract -> native artifacts -> offline acceptance tests`。
第五句：实现规模，`10 compile targets`、`5 import source types`、`10 deterministic assertions`。
第六句：演示内容，跨目标编译、loss report、reverse import、offline validation。
第七句：结论，工具适合不能修改 runtime、但希望统一治理策略的团队。

### 2.10 ICSE demo 版投稿前检查清单

- 论文、仓库、视频中的数字完全一致
- 工具安装路径在全新环境中可复现
- 至少一个 demo case 从 authoring 到 testing 走完整条链
- 所有截图、命令、artifact 名称与仓库真实输出一致
- 声称的 compile targets 和 importers 都能在视频中被真实展示或在 artifact 中可见

---

## 3. FSE 长文版

### 3.1 投稿定位

这个版本建议按“长篇研究论文”来组织，而不是先把自己锁死在尚未公开 CFP 的 `Industry Track` 上。

推荐定位：

- 主问题是**异构 agent 治理的可移植性与可验证性**
- 主贡献是**runtime-free contract compilation + loss reporting + deterministic output validation**
- 主实证是**表达能力、round-trip fidelity、缺陷检测、维护成本**

后续如果 `FSE 2027 Industry Track` 开放，且更适合，再把这版压缩并强化工业 deployment 叙事。

### 3.2 推荐标题

首选：

`Zero-Intrusion Contract Compilation for Governing Heterogeneous AI Agents`

备选：

`Single-Source Agent Governance through Runtime-Free Contract Compilation and Deterministic Output Validation`

### 3.3 中心论点

> Heterogeneous AI agent ecosystems need a governance layer that is portable across platforms, does not require runtime modification, and remains auditable through deterministic post-hoc validation.

### 3.4 建议保留的贡献

建议收敛到 4 点：

1. 问题 formulation：提出 `zero-intrusion agent governance` 这一软件工程问题，并明确其与 runtime enforcement 的边界差异。
2. 系统设计：设计 `GovernSpec` source schema、`IIR`、target-specific compilation 和 compile-time loss reporting。
3. 双向工作流：实现 `10 compile targets` 与 `5 import source types`，支持从 source contract 到 native artifact，再从 artifact 回到 structured contract。
4. 确定性验收：提供 `10` 种不依赖模型的离线断言，用于对 agent 产出进行 post-hoc governance checks。

避免写成：

- `首次`
- `证明`
- `理论贡献`

### 3.5 长文结构建议

#### 1. Introduction

写作目标：

- 用一个“同一团队同时用多个 agent 工具”的真实工程场景开头。
- 指出现有治理实践通常有两条路线：
  - runtime-centered governance
  - artifact-centered native instructions
- 指出空缺不在“有没有安全系统”，而在“有没有一种统一、低侵入、可移植的治理 authoring layer”。
- 明确本文研究问题：

> How can we author governance contracts once, propagate them across heterogeneous agent-native artifacts without runtime modification, and still obtain auditable post-hoc validation of generated outputs?

收尾给 4 条贡献。

#### 2. Background and Problem Formulation

建议分 3 小节：

##### 2.1 Runtime-centered governance

放研究论文：

- `Policy Compiler for Secure Agentic Systems`
- `Agent Behavioral Contracts`
- 其他真正 peer-reviewed 的 runtime monitoring / policy compilation 论文

这里要明确：

- 它们解决的是 action-time enforcement 或 policy evaluation
- 本文解决的是 artifact-time propagation 和 output-time validation

##### 2.2 Artifact-native governance in practice

放生态系统和工程现实：

- `AGENTS.md`
- `CLAUDE.md`
- `Cursor Rules`
- structured output payloads
- `OSSA`

重点说明：现代 agent 工具链已经有大量“原生 artifact channel”，但缺少统一 authoring 和 loss-aware translation。

##### 2.3 Problem formulation

定义四个概念：

- source contract
- target artifact
- expressibility
- compile-time loss report

这一节的目标不是形式化得多漂亮，而是把问题边界切干净。

#### 3. System Design

建议按真正的系统链路写：

##### 3.1 Authoring schema

- contract fields
- imports / packs
- deny-by-default permissions
- deterministic acceptance tests

##### 3.2 Intermediate representation

- 为什么需要 `IIR`
- `IIR` 承担哪些 normalization 责任
- 为什么 loss reporting 不能直接在 source schema 上做

##### 3.3 Target-specific compilation

- instruction documents
- IDE rules
- structured outputs
- machine-readable governance plans

建议把 `10 compile targets` 先按“target family”聚类，再落到具体 targets。

##### 3.4 Compile-time loss reporting

这是长文里值得单独成节的地方，但不要写成“重要理论贡献”。

更稳的定位：

- 一个 practical analysis construct
- 一个帮助用户理解 target expressibility mismatch 的机制

建议定义：

```text
loss(C, t) = information present in source contract C
             but not faithfully representable in target t
```

可以再细分 loss category：

- permission loss
- gate loss
- constraint loss
- test loss

##### 3.5 Reverse import

- precise import，针对编译产物
- heuristic import，针对手写 artifact
- 为什么 round-trip fidelity 只在 `5 import source types` 上评估

##### 3.6 Offline acceptance testing

把 `10` 种断言完整列出来，并按三类组织：

- structural
- content-based
- quantitative / JSON-specific

这里明确一条限制：

- 它们验证的是 contract-compliance signals，不是 semantic correctness。

#### 4. Evaluation

推荐改成 4 个正式 RQ。

##### RQ1. Expressibility and Loss Reporting

研究问题：

> How much of a source contract can each representative target family faithfully encode, and what loss categories are reported at compile time?

建议评估 `6` 个 representative targets：

- `agents-md`
- `claude-md`
- `cursor-rules`
- `openai-structured`
- `gemini-structured`
- `mcp-plan`

建议数据集：

- 最小可行：`20` 个 contracts
- 更稳版本：`24-30` 个 contracts，覆盖权限、约束、gates、output schema、tests 的正交组合

建议指标：

- field-level preservation
- category-level loss count
- per-target loss distribution

建议展示：

- heatmap
- loss category breakdown

注意：

- 不要把 preservation 简化成唯一一个比率然后过度解读
- 更稳的是 `field-level matrix + summarized rate`

##### RQ2. Round-Trip Fidelity

研究问题：

> How faithfully can structured contracts be reconstructed from compiled artifacts and from hand-authored artifacts?

范围必须写清楚：

- 只评估有 importers 的 `5 source types`
- 分开报告：
  - compiler-produced artifacts
  - hand-authored artifacts

建议指标：

- exact field match
- normalized field match
- artifact family specific fidelity

建议标注协议：

- 两名标注者独立判断难例
- 报告 `Cohen's kappa`

##### RQ3. Offline Assertion Effectiveness

研究问题：

> What classes of governance defects can deterministic offline assertions detect reliably?

建议样本：

- 最小可行：`50` 个 outputs
- 更稳版本：`80-100` 个 outputs

建议 defect categories：

- missing required sections
- forbidden content present
- regex mismatch
- length violation
- malformed JSON / schema mismatch
- missing JSON path
- insufficient JSON array size

建议报告：

- precision
- recall
- per-assertion-family breakdown

必须在 discussion 中明确：

- 对语义错误和事实错误，recall 有天然上界。

##### RQ4. Authoring and Maintenance Cost

这是最建议替换原“Deployment Friction vs Edictum/AgentContract”的地方。

更公平的研究问题：

> Compared with hand-maintained per-platform artifacts, how much authoring and maintenance effort does a single-source contract workflow save?

主 baseline：

- 手写 `AGENTS.md`
- 手写 `CLAUDE.md`
- 手写 `.mdc`
- 手写 structured output JSON

可选的补充 comparison：

- 对 runtime-centered systems 做 qualitative discussion

建议指标：

- artifacts maintained per task
- duplicated policy statements
- files touched per policy update
- time to propagate one policy change across platforms
- reviewer-visible diff size

这一组指标更贴近你的真实价值主张，也更不容易被说成 apples-to-oranges。

#### 5. Discussion

建议保留 4 个讨论点：

##### 5.1 Advisory governance vs enforced governance

明确：

- instruction artifacts 是 advisory channel
- runtime monitors 是 enforcement channel
- 两者可以叠加

##### 5.2 When GovernSpec is the right tool

适合：

- 无法控制 runtime
- 需要跨平台一致治理
- 需要本地、可审计、可 review 的 source contract

不适合：

- 必须 fail-closed
- 必须在 tool invocation 时阻断高风险动作
- 需要深度语义判断

##### 5.3 Target churn and backend maintenance

这是现实系统一定会被问到的问题：

- target formats 会变
- import heuristics 会漂移
- compile backends 需要持续维护

把它正面写出来，会显得更诚实。

##### 5.4 Practical role of loss reporting

强调 `loss report` 的工程意义：

- 让用户知道“哪里丢了”
- 支持目标选择
- 支持双轨部署，例如 instruction artifact + runtime guard

#### 6. Threats to Validity

建议保留三类：

- 内部有效性
  - preservation 标注主观性
  - hand-authored artifact 质量差异
- 外部有效性
  - contracts 和 outputs 的样本覆盖有限
  - target ecosystem 持续变化
- 构建有效性
  - 当前系统评估的是 governance portability 和 auditability，不是 security completeness

#### 7. Conclusion

结论只收 3 点：

1. `single-source contract + native artifact compilation` 是一种可行的 agent governance 工作流
2. `loss reporting` 能帮助用户理解 heterogeneous targets 的表达差异
3. `deterministic offline acceptance tests` 为 runtime-free governance 提供了可审计的补充层

### 3.6 FSE 长文版建议图表

- `Figure 1`：system overview
- `Figure 2`：target family and artifact mapping
- `Figure 3`：example loss report across targets
- `Table 1`：source fields vs representative targets expressibility matrix
- `Table 2`：evaluation datasets
- `Figure 4`：RQ1 heatmap
- `Figure 5`：RQ2 fidelity results
- `Figure 6`：RQ3 assertion performance
- `Figure 7`：RQ4 maintenance-cost comparison

### 3.7 FSE 长文版最低证据门槛

如果要把这版当“可投稿长文”，至少需要：

- 一个稳定的 contract benchmark
- 一套明确的 artifact corpus
- 双标注协议
- 可复现实验脚本
- 对 target families 的代表性说明

如果这些还没有齐，不建议急着投长文。

### 3.8 FSE 长文版摘要骨架

第一句：异构 agent 生态让治理规则分散在多种 native artifacts 中。
第二句：现有研究多关注 runtime-time monitoring 或 policy enforcement，较少关注不修改 runtime 的统一 authoring 与 translation。
第三句：本文提出 `GovernSpec`，一种 `local-first`、`zero-intrusion` 的 contract compilation framework。
第四句：系统设计，`source schema + IIR + target-specific compilation + loss reporting + reverse import + deterministic offline assertions`。
第五句：实现规模，`10 compile targets`、`5 import source types`、`10 assertions`。
第六句：评估问题，expressibility、round-trip fidelity、assertion effectiveness、maintenance cost。
第七句：结论，GovernSpec 适合作为 heterogeneous agent toolchains 上层的 governance authoring layer，而不是 runtime enforcement 的替代品。

---

## 4. 两个版本的共同禁区

### 4.1 不要再写的句子

- `GovernSpec enforces behavior without runtime modification.`
- `GovernSpec is more secure than runtime interception approaches.`
- `This is the first work to formalize constraint loss.`
- `10 native tools are already supported.`

### 4.2 建议替代句

- `GovernSpec propagates governance intent through native agent artifacts.`
- `GovernSpec complements runtime-centered governance by covering settings where runtime modification is unavailable or undesirable.`
- `We operationalize compile-time information loss as a practical reporting mechanism.`
- `The current prototype implements 10 compile targets and 5 import source types.`

### 4.3 相关工作写作禁区

- 不要把产品、博客、开源项目和 peer-reviewed 论文写成同一证据等级。
- 不要把不同系统的 threat model 混成一个量化比较表。
- 不要在 related work 中偷换概念，把“policy enforcement”直接等同于“artifact compilation”。

---

## 5. 推荐执行顺序

### 如果目标是尽快形成可投稿材料

1. 先写 `ICSE demo 版`
2. 同步补齐 benchmark、artifact corpus、annotation protocol
3. 再扩成 `FSE 长文版`

### 原因

- `ICSE demo` 对工具成型度、可演示性和 artifact 清晰度要求高，但对大规模研究结论要求相对低
- 这与你当前仓库成熟度更匹配
- 写 `ICSE demo` 的过程，本身就会把 `FSE` 长文最需要的图、案例、workflow 和实验脚手架准备出来

---

## 6. 现在就可以开始写的内容

优先级从高到低：

1. `ICSE demo` 的 `Introduction`、`Tool Overview`、`Demo Scenario`
2. `Figure 1` workflow 图
3. `Table 1` representative targets matrix
4. 长文版的 `Section 3 System Design`
5. RQ1-RQ4 的实验协议草案

---

## 7. 写作时的最终口径

如果你只记住一句话，建议统一成下面这句：

> GovernSpec is a local-first, zero-intrusion contract compiler for heterogeneous AI agent ecosystems, paired with deterministic offline acceptance testing and explicit compile-time loss reporting.
