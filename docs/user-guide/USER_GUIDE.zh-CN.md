<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# PAISL v0.1.0 用户使用手册

> Personal AI Standards Library · User Guide  
> 文档版本：1.1 · 适用软件版本：PAISL v0.1.1 · 语言：简体中文  
> 状态：基于已验收仓库设计的使用说明；具体 Agent 兼容性需在实际环境中验证。

## 目录

1. [项目介绍](#01-项目介绍)
2. [安装与快速开始](#02-安装与快速开始)
3. [标准库结构与标准发现](#03-标准库结构与标准发现)
4. [内置 Skills 使用指南](#04-内置-skills-使用指南)
5. [Agent 集成与 Prompt 规范](#05-agent-集成与-prompt-规范)
6. [三个可复现案例](#06-三个可复现案例)
7. [新增与修改标准](#07-新增与修改标准)
8. [校验与故障排查](#08-校验与故障排查)
9. [治理、版本和版权](#09-治理版本和版权)
10. [FAQ 与验收清单](#10-faq-与验收清单)

---

## 01 项目介绍

### 1.1 PAISL 是什么

PAISL（Personal AI Standards Library，个人 AI 标准库）是开放、双语、机器可读的标准与实践库，目标是改善人类向 AI 表达需求的方式，以及 AI 产出的清晰度、结构性、可验证性和复用性。

PAISL **不是**大模型、自动化工作流引擎、通用提示词市场或正式标准机构的认证服务。v0.1.0 的交付物是一个基于 Git 文件的标准注册表、可供 Agent 阅读的 Skills、Schema 和结构校验工具。

### 1.2 五个关键概念

| 概念        | 含义                        | 位置                             |
| --------- | ------------------------- | ------------------------------ |
| Standard  | 有 ID、版本、规则、来源和局限的规范条目     | `standards/**/*.yaml`          |
| Catalog   | 标准 ID 到文件路径的索引            | `catalog/standards.yaml`       |
| Schema    | 约束标准 YAML 数据结构的契约         | `schemas/standard.schema.json` |
| Skill     | 告诉 Agent 如何在任务中使用标准的操作流程  | `skills/*/SKILL.md`            |
| Validator | 检查 Schema、目录、ID 等结构一致性的脚本 | `scripts/validate.py`          |

**关键区别**：Standard 规定“应遵循什么”，Skill 规定“如何在任务中使用”。一个 Skill 可以引用多个 Standard；一个 Standard 也可以被多个 Skill 使用。

### 1.3 v0.1.0 的能力边界

**已提供**：12 个 `draft` 标准、5 个 Skill、双语字段、Catalog、JSON Schema、Python 校验器、GitHub Actions 和贡献治理说明。

**未提供**：MCP Server、REST/GraphQL 服务、自动 Skill 安装、自动事实核验、标准语义冲突检测、执行效果自动打分和官方第三方标准认证。

### 1.4 适用人群与典型任务

- 内容作者：改善技术说明、文档结构和表达清晰度。
- 软件工程师：将规范作为 Agent 的可读取约束。
- 研究者：用结构化思考和证据审查规范 AI 输出。
- 维护者：扩展标准条目并维持目录、版本和引用一致性。

## 02 安装与快速开始

### 2.1 前置条件

建议使用 Python 3.12、Git，以及能够读取本地文件的 AI Agent 或编辑器。macOS/Linux 的命令如下；Windows 用户可使用 PowerShell 或 WSL，并替换虚拟环境激活命令。

### 2.2 获取仓库

若仓库已存在，进入根目录：

```bash
cd personal-ai-standards
```

若尚未克隆，使用自己的 GitHub 仓库地址（以下是占位符，不是实际可用地址）：

```bash
git clone https://github.com/<YOUR_ACCOUNT>/personal-ai-standards.git
cd personal-ai-standards
```

### 2.3 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Windows PowerShell：

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` 包含 PyYAML（解析 YAML）与 jsonschema（校验 JSON Schema Draft 2020-12）。

### 2.4 校验仓库

```bash
python scripts/validate.py
```

在仓库内容完整且符合 v0.1.0 契约时，**预期**看到：

```text
=== PAISL Validation Report ===
Standards checked: 12
Errors: 0
Warnings: 0

Validation PASSED
```

这是预期示例，不代表本手册已经在你的环境中运行过校验。

### 2.5 第一次手动使用

1. 打开 `catalog/standards.yaml`，查找 `PAISL-COMM-001`。
2. 按 `path` 字段打开 `standards/communication/ste-writing.yaml`。
3. 阅读 `rules` 和 `limitations`。
4. 打开 `skills/ste-writing/SKILL.md`，按照其中的流程修改一段技术说明。
5. 对照原文检查语义是否保留。

完成这五步，即完成不依赖 MCP 的最小闭环。

## 03 标准库结构与标准发现

### 3.1 仓库目录

```text
personal-ai-standards/
├── README.md
├── README.zh-CN.md
├── AGENTS.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
├── LICENSE-DOCS
├── requirements-dev.txt
├── catalog/
│   ├── categories.yaml
│   └── standards.yaml
├── schemas/
│   └── standard.schema.json
├── standards/
│   ├── communication/
│   ├── reasoning/
│   ├── productivity/
│   ├── visualization/
│   ├── verification/
│   └── engineering/
├── skills/
│   ├── standard-discovery/SKILL.md
│   ├── ste-writing/SKILL.md
│   ├── structured-thinking/SKILL.md
│   ├── ai-output-review/SKILL.md
│   └── visual-explanation/SKILL.md
├── scripts/
│   └── validate.py
├── docs/
│   ├── architecture.md
│   ├── governance.md
│   └── agent-integration.md
└── .github/
    ├── workflows/validate.yml
    ├── ISSUE_TEMPLATE/standard-proposal.md
    └── pull_request_template.md
```

### 3.2 标准 ID

ID 格式为 `PAISL-<CATEGORY>-<NUMBER>`，例如 `PAISL-COMM-001`。分类前缀包括 `COMM`（沟通）、`REAS`（推理）、`PROD`（生产力）、`VIS`（可视化）、`VER`（核验）、`ENG`（工程）。**ID 是稳定身份，`version` 是该条目内容的版本。**

### 3.3 12 个初始标准

| ID             | 标准/实践              | 文件                                                |
| -------------- | ------------------ | ------------------------------------------------- |
| PAISL-COMM-001 | STE 启发式技术写作        | `standards/communication/ste-writing.yaml`        |
| PAISL-COMM-002 | BLUF 结论先行          | `standards/communication/bluf.yaml`               |
| PAISL-COMM-003 | Google 开发者文档风格映射   | `standards/communication/google-doc-style.yaml`   |
| PAISL-REAS-001 | 第一性原理              | `standards/reasoning/first-principles.yaml`       |
| PAISL-REAS-002 | MECE               | `standards/reasoning/mece.yaml`                   |
| PAISL-REAS-003 | OODA               | `standards/reasoning/ooda.yaml`                   |
| PAISL-REAS-004 | 金字塔原理              | `standards/reasoning/pyramid-principle.yaml`      |
| PAISL-PROD-001 | GTD                | `standards/productivity/gtd.yaml`                 |
| PAISL-VIS-001  | 信息设计               | `standards/visualization/information-design.yaml` |
| PAISL-VIS-002  | 渐进式可视化解释           | `standards/visualization/visual-explanation.yaml` |
| PAISL-VER-001  | 证据驱动事实核验           | `standards/verification/fact-checking.yaml`       |
| PAISL-ENG-001  | OWASP ASVS 启发式安全审查 | `standards/engineering/owasp-asvs.yaml`           |

### 3.4 YAML 字段说明

标准条目通常包含：`id`、`version`、`status`、`kind`、`category`、`name`、`description`、`purpose`、`scope`、`sources`、`rules`、`limitations` 和可选的 `tags`。`name`、`description`、`purpose`、`scope`、规则说明和局限说明采用 `en` 与 `zh-CN` 双语对象。

`status: draft` 表示初稿，**不代表**已获来源机构认证。`sources` 提供追溯线索，URL 存在不等于证据已经被验证。

### 3.5 使用命令查询目录

```bash
# 查看 Catalog
cat catalog/standards.yaml

# 查找某个标准 ID
grep -R "PAISL-COMM-001" catalog standards skills

# 列出所有标准文件
find standards -type f -name '*.yaml' | sort
```

这些命令只读取文件，不修改仓库。

## 04 内置 Skills 使用指南

### 4.1 Skill 使用原则

v0.1.0 的 Skill 是仓库中的 Markdown 操作说明，**不是**安装后就能自动运行的可执行程序。Agent 需要能够读取对应文件，并根据其步骤完成任务。具体是否自动发现 `SKILL.md`，取决于 Agent Runtime 的实现和配置。

| Skill                 | 使用时机     | 引用标准                          | 预期产物         |
| --------------------- | -------- | ----------------------------- | ------------ |
| `standard-discovery`  | 不确定选哪个标准 | Catalog 中相关标准                 | 候选 ID、适用性、局限 |
| `ste-writing`         | 优化技术写作   | COMM-001、COMM-003             | 修改文本、变更说明、歧义 |
| `structured-thinking` | 拆解复杂问题   | REAS-001/002/003/004、COMM-002 | 分析结构、选项、结论   |
| `ai-output-review`    | 审查 AI 输出 | VER-001、COMM-001/002、REAS-002 | 问题清单、修订建议    |
| `visual-explanation`  | 规划视觉讲解   | VIS-001、VIS-002               | 分镜、标注、说明     |

表中省略了重复的 `PAISL-` 前缀。

### 4.2 通用执行流程

1. 明确任务目标、输入与限制。
2. 选择 Skill，读取 `skills/<name>/SKILL.md`。
3. 在 Catalog 中解析 Skill 引用的标准 ID。
4. 读取标准 YAML 的规则、来源与局限。
5. 执行 Skill 步骤。
6. 输出结果、变更说明及未解决问题。
7. 人工核查结果是否符合任务目标。

### 4.3 Skill 选择示例

- “把部署手册写清楚” → `ste-writing`。
- “比较两种系统架构” → `structured-thinking`。
- “这份 AI 报告有没有事实依据” → `ai-output-review`。
- “设计一张教学示意图的内容” → `visual-explanation`。
- “我不知道该选什么规范” → `standard-discovery`。


### 4.6 security-review：应用安全初步审查

**引用标准：** PAISL-ENG-001

**适用场景：**

- 应用架构安全评审
- API 身份认证与授权设计检查
- 数据流与信任边界分析
- Agent 工具访问安全评估

**使用方法：**

1. 阅读 `skills/security-review/SKILL.md`。
2. 通过 Catalog 读取 PAISL-ENG-001。
3. 提供待审查系统的架构与约束。
4. 要求 Agent 区分事实、假设和未知项。
5. 审查风险发现及验证建议。

**示例 Prompt：**

> 请按照 PAISL 的 security-review Skill，
> 对以下系统架构进行初步安全审查。
>
> 系统包含 Web 前端、API Gateway、
> Agent Runtime、PostgreSQL 和外部 LLM API。
>
> 请识别信任边界、认证与授权假设、
> 潜在安全风险及待验证事项。
>
> 不要假设未描述的安全控制已经实现。
> 不要宣称完成 OWASP ASVS 合规认证。

**预期输出：**

- 系统上下文
- 信任边界
- 安全观察与风险
- 未验证假设
- 建议行动
- 引用的 PAISL 标准及规则

### 4.7 task-clarification：任务澄清

**引用标准：** PAISL-PROD-001

**适用场景：**

- 项目计划整理
- 模糊任务分解
- 会议待办提取
- Agent 执行任务准备
- 每周任务规划

**使用方法：**

1. 阅读 `skills/task-clarification/SKILL.md`。
2. 通过 Catalog 读取 PAISL-PROD-001。
3. 提供原始任务清单。
4. 要求 Agent 明确目标和下一步行动。
5. 检查是否编造负责人、截止日期或依赖。

**示例 Prompt：**

> 请按照 PAISL 的 task-clarification Skill，
> 整理以下任务：
>
> - 完善 PAISL 用户手册
> - 检查标准与 Skill 的引用关系
> - 准备下一版本的产品需求
>
> 请区分项目目标、下一步行动、
> 等待事项和需要澄清的问题。
>
> 未提供的负责人和截止日期标记为
> "未指定"，不要自行编造。

**预期输出：**

- 目标摘要
- 下一步行动清单
- 项目与预期成果
- 等待事项
- 待澄清问题
- 引用的 PAISL 标准及规则

### 4.8 Standard 与 Skill 的关系

Standard 定义可复用规则。

Skill 定义 Agent 如何执行一类任务。

一个 Skill 可以引用多个 Standard，
一个 Standard 也可以被多个 Skill 引用。

没有专用 Skill 的 Standard 仍可以通过
Catalog 被直接发现和使用。

详见 `docs/governance.md`。


## 05 Agent 集成与 Prompt 规范

### 5.1 集成模式

**模式 A：手动文件引用（推荐起点）**。将 PAISL 仓库置于 Agent 可访问的工作区，在 Prompt 中写明文件路径与标准 ID。适合 OpenCode、其他代码 Agent 或支持本地文件读取的工作环境。

**模式 B：项目级指令**。将 `AGENTS.md` 的适用规则引入目标项目的 Agent 指令中，明确 PAISL 仓库位置。注意目标工具是否支持跨目录读取及其指令加载机制。

**模式 C：复制 Skill**。仅在目标 Runtime 的 Skill 规范兼容时，将对应 `SKILL.md` 复制到其指定位置；不可假定所有 Runtime 都遵循相同格式。

### 5.2 通用 Prompt 模板

```text
你正在处理一个需要遵循 PAISL 的任务。

PAISL 仓库位置：<PAISL_ROOT>
任务目标：<TASK>
输入材料：<INPUT>
约束：<CONSTRAINTS>

请执行：
1. 阅读 <PAISL_ROOT>/AGENTS.md。
2. 阅读 <PAISL_ROOT>/skills/<SKILL_NAME>/SKILL.md。
3. 从 catalog/standards.yaml 解析 Skill 引用的标准 ID。
4. 阅读对应 standards/**/*.yaml 的规则与局限。
5. 按 Skill 步骤完成任务，不要编造未读取的规则。
6. 输出最终结果、应用的标准 ID、重要修改和不确定项。
7. 不要声称获得第三方标准机构的官方认证。
```

### 5.3 OpenCode 使用示例

在 OpenCode 能访问 PAISL 仓库的工作区内，发送以下任务（路径按实际布局调整）：

```text
请先读取 ./personal-ai-standards/AGENTS.md，
再读取 ./personal-ai-standards/skills/ste-writing/SKILL.md。

从 Catalog 找到 PAISL-COMM-001 和 PAISL-COMM-003，
读取对应 YAML 并根据规则改写下方说明。
保留技术事实、命令和警告，输出修改说明。

原文：<粘贴原文>
```

这是一种**基于文件读取的操作方法**，不是声称 v0.1.0 已具备 OpenCode 原生插件或自动发现功能。

### 5.4 Agent 输出建议格式

```markdown
## 结果
<最终内容>

## 应用标准
- PAISL-...：<应用位置与方式>

## 修改说明
- <改动及理由>

## 不确定项
- <需要人工确认的问题；没有则写“无”>
```

## 06 三个可复现案例

> 复现原则：同一输入、同一 Skill、同一标准版本、同一 Prompt。大模型的措辞可能不同，因此本版采用**行为检查**，不要求逐字匹配。v0.1.0 尚无自动评分器。

### 案例 A：技术文档规范化

**目标**：将含混的部署说明改写为可执行、清晰的步骤。

**标准**：`PAISL-COMM-001`、`PAISL-COMM-003`。  
**Skill**：`skills/ste-writing/SKILL.md`。

**测试输入**（保存为 `examples/case-a-input.md`，或直接粘贴）：

```text
服务在部署时一般需要先弄好环境，数据库也要能用，
然后把配置填一下就可以启动了。如果起不来，
可能是端口或密码的问题，处理一下再试。
```

**执行 Prompt**：

```text
阅读 PAISL 的 AGENTS.md、skills/ste-writing/SKILL.md，
以及 PAISL-COMM-001、PAISL-COMM-003 的 YAML。

请把以下部署说明改写为清晰的操作步骤。
不要凭空添加端口号、数据库类型、命令或凭据。
对缺失的前置条件使用“待确认”标记。
输出：改写结果、修改说明、待确认事项、引用标准 ID。

输入：
服务在部署时一般需要先弄好环境，数据库也要能用，
然后把配置填一下就可以启动了。如果起不来，
可能是端口或密码的问题，处理一下再试。
```

**合格输出示意**（示例，不是唯一标准答案）：

```markdown
## 部署步骤
1. 确认运行环境符合部署要求（具体版本待确认）。
2. 确认数据库服务可连接（连接方式待确认）。
3. 填写应用配置（配置项及位置待确认）。
4. 按项目提供的启动命令启动服务（命令待确认）。
5. 如果启动失败，检查端口占用和认证配置；
   不要在日志或工单中泄露密码。

## 待确认
- 运行环境及版本
- 数据库类型与连接要求
- 配置文件位置及字段
- 启动命令、监听端口和日志位置
```

**人工验收**：

- [ ] 保留“环境 → 数据库 → 配置 → 启动 → 排错”的原有流程。
- [ ] 将模糊表达转为明确动作。
- [ ] 未编造命令、版本或端口。
- [ ] 明确列出缺失信息。
- [ ] 列出实际读取和应用的标准 ID。

### 案例 B：复杂技术方案的结构化分析

**目标**：在有限资源下比较单体架构和微服务架构。

**标准**：`PAISL-REAS-001`、`PAISL-REAS-002`、`PAISL-REAS-003`、`PAISL-REAS-004`、`PAISL-COMM-002`。  
**Skill**：`skills/structured-thinking/SKILL.md`。

**测试输入**：

```text
团队 3 人，计划 8 周交付一个内部知识管理 MVP。
主要功能是上传文档、全文搜索、AI 问答和访问控制。
日活预计 50 人。需要比较单体架构与微服务架构，
选择初期方案并说明未来拆分条件。
```

**执行 Prompt**：

```text
阅读 PAISL 的 AGENTS.md、structured-thinking Skill，
以及 Skill 引用的所有标准 YAML。

针对以下需求，比较单体架构与微服务架构：
团队 3 人，8 周交付内部知识管理 MVP；功能包括
上传文档、全文搜索、AI 问答和访问控制；日活约 50。

要求：
1. 先给出有条件的建议。
2. 分开列出已知事实、假设和未知项。
3. 从交付速度、复杂度、可靠性、扩展性、成本分析。
4. 明确未来从单体拆分的可观察触发条件。
5. 不能把假设写成已经证实的事实。
6. 列出使用的 PAISL 标准 ID。
```

**合格输出要点**：初期通常倾向模块化单体以降低三人团队八周交付的协调与运维负担；但这属于**基于给定条件的设计判断**，不是普遍结论。应说明访问控制与文档处理的模块边界，并提出可测量的拆分触发条件，例如独立扩缩容需求、资源隔离要求、团队独立发布需求或可观测的性能瓶颈。

**人工验收**：

- [ ] 有明确结论与适用条件。
- [ ] 已知事实、假设和未知项分别列出。
- [ ] 两种架构使用同一组比较维度。
- [ ] 说明至少两个潜在风险及缓解措施。
- [ ] 提供未来重新评估的触发条件。
- [ ] 没有伪造性能基准、成本数据或来源。

### 案例 C：AI 研究报告的事实核验

**目标**：识别报告中的未经证实的定量结论和过度推断。

**标准**：`PAISL-VER-001`、`PAISL-COMM-001`、`PAISL-COMM-002`、`PAISL-REAS-002`。  
**Skill**：`skills/ai-output-review/SKILL.md`。

**测试输入**（为测试构造的虚拟陈述，不是事实）：

```text
研究报告：2026 年所有企业都已经部署 AI Agent。
某项未注明来源的调查显示，使用 Agent 后生产效率
平均提高 300%。因此所有企业应立即取消人工审核，
将所有业务决策交给 Agent。
```

**执行 Prompt**：

```text
阅读 PAISL 的 AGENTS.md、ai-output-review Skill，
以及引用的标准 YAML。

请审查下面这段研究报告：
“2026 年所有企业都已经部署 AI Agent。
某项未注明来源的调查显示，使用 Agent 后生产效率
平均提高 300%。因此所有企业应立即取消人工审核，
将所有业务决策交给 Agent。”

要求：
1. 将可核验事实主张、价值判断和建议分开。
2. 为每条事实主张标注证据状态。
3. 没有来源时写“未验证”，不得伪造引用。
4. 识别从数据到建议的逻辑跳跃。
5. 提供保守、可追溯的修订版本。
6. 列出 PAISL 标准 ID 和剩余不确定性。
```

**合格输出要点**：指出“所有企业”属于未经证实的全称判断；“平均提高 300%”缺少样本、指标定义、测量方法和来源；“取消人工审核”并不能由前两条主张逻辑推出。若 Agent 没有被授权或没有能力检索外部证据，应标记为“未验证”，而非直接断言真假。

**人工验收**：

- [ ] 至少识别上述三类问题。
- [ ] 区分“缺少证据”和“已经证明错误”。
- [ ] 未编造调查、机构、论文或链接。
- [ ] 保留人工审批和风险控制的必要性作为待评估要求。
- [ ] 给出可核验的后续研究问题。

### 6.4 案例执行记录模板

每次测试建议保存一份记录：

```yaml
case_id: case-a
paisl_release: v0.1.0
skill: ste-writing
standards:
  - PAISL-COMM-001
  - PAISL-COMM-003
agent_runtime: "<填写实际工具及版本>"
model: "<填写实际模型>"
executed_at: "<ISO-8601 时间>"
input_file: "<输入文件路径>"
output_file: "<输出文件路径>"
reviewer: "<人工审查者>"
result: "pass | fail | needs_review"
notes: "<具体观察>"
```

这只是人工记录模板，**不是** v0.1.0 已实现的自动评测数据格式或 API。

## 07 新增与修改标准

### 7.1 标准新增流程

1. 阅读 `CONTRIBUTING.md` 与 `docs/governance.md`。
2. 选择合适的分类和未占用的 ID。
3. 在 `standards/<category>/` 创建 YAML。
4. 按 `schemas/standard.schema.json` 填写必需字段。
5. 在 `catalog/standards.yaml` 添加 ID 与路径。
6. 运行 `python scripts/validate.py`。
7. 提交 PR，附上来源、版权说明和变更理由。

### 7.2 最小示例（演示，不要与现有 ID 冲突）

下面假设 `PAISL-COMM-004` 尚未使用，演示结构，不建议未经来源审查直接纳入正式标准库：

```yaml
id: PAISL-COMM-004
version: 0.1.0
status: draft
kind: practice
category: communication
name:
  en: Example Communication Practice
  zh-CN: 示例沟通实践
description:
  en: Clarify the audience before writing.
  zh-CN: 写作前明确目标读者。
purpose:
  en: Improve audience alignment.
  zh-CN: 提高内容与读者的匹配程度。
scope:
  en: General technical communication.
  zh-CN: 一般技术沟通。
sources:
  - title: Example source (replace before submission)
    url: https://example.org/
    type: secondary
rules:
  - id: R001
    instruction:
      en: Identify the intended audience.
      zh-CN: 明确目标读者。
    rationale:
      en: Audience needs affect presentation.
      zh-CN: 读者需求影响表达方式。
    severity: should
limitations:
  - en: Example only; source not verified.
    zh-CN: 仅供演示；来源未核验。
tags:
  - communication
```

请勿将 `example.org` 当作真实证据来源。

### 7.3 修改原则

- 已发布标准 ID 不应随意重用或改名。
- 修改规则含义时应评估版本影响。
- 同步维护英文和中文文本。
- 变更来源时记录依据，不得声称外部标准机构认可。
- `validate.py` 通过仅说明结构满足当前校验要求，不说明语义正确。

## 08 校验与故障排查

### 8.1 本地校验

```bash
python scripts/validate.py
```

校验覆盖：JSON Schema 结构、标准 ID 与 Catalog 对应关系、目录分类匹配、重复 ID、重复规则 ID、来源 URL 基本格式，以及是否存在未登记 YAML。

### 8.2 GitHub Actions

工作流：`.github/workflows/validate.yml`。在 `push`、`pull_request` 或手动触发时，使用 Python 3.12 安装开发依赖并运行校验器。CI 通过不能替代人工语义和版权审查。

### 8.3 常见问题

| 现象                                | 可能原因               | 处理方法                                     |
| --------------------------------- | ------------------ | ---------------------------------------- |
| `ModuleNotFoundError: yaml`       | 未安装 PyYAML         | 激活虚拟环境并安装依赖                              |
| `ModuleNotFoundError: jsonschema` | 未安装 jsonschema     | 运行 `pip install -r requirements-dev.txt` |
| `Missing standard file`           | Catalog 路径错误       | 对照真实路径修正 `path`                          |
| `Uncataloged standard`            | 新 YAML 未加入 Catalog | 添加 Catalog 条目                            |
| `ID/category mismatch`            | ID 前缀与分类不一致        | 检查 `id` 和 `category`                     |
| `duplicate rule IDs`              | 同一标准内重复规则 ID       | 重新分配 `R001` 等编号                          |
| `Validation FAILED`               | 一个或多个结构错误          | 阅读全部 `ERROR:` 行并逐项修正                     |
| Agent 找不到 Skill                   | 工作目录或读取权限问题        | 显式提供文件路径，确认 Runtime 可读取                  |
| Agent 编造规则                        | 未读取标准文件            | 要求逐项报告已读取的文件和标准 ID                       |

### 8.4 不属于本版本校验范围的事项

- 规则与原始标准的语义一致性。
- 规则间的逻辑冲突。
- 来源链接当前是否可访问、是否可信。
- Skill 是否真正改善任务质量。
- 不同模型是否给出一致结果。
- Agent 对恶意外部内容的防护有效性。

## 09 治理、版本和版权

### 9.1 状态流转

`draft → review → verified → deprecated`。

`verified` 表示 PAISL 项目内部按治理流程审查，不代表 ASD、Google、OWASP 或其他机构的官方认证。

### 9.2 版本策略

- **仓库版本**：例如 Git Tag `v0.1.0`，表示一次整体发布。
- **标准版本**：YAML 内 `version: 0.1.0`，表示条目自身的版本。
- **Skill 版本**：`SKILL.md` Frontmatter 中的版本，表示操作说明的版本。

三者可能在未来独立演进。当前 v0.1.0 没有实现自动依赖锁定或兼容性求解。

### 9.3 版权与引用

- 原创代码：MIT。
- 原创文档、Skills、独立编写的摘要：CC BY 4.0（以仓库声明为准）。
- 第三方标准、原文和商标：遵守各自许可。

PAISL 中的“STE 启发式”“OWASP ASVS 启发式”等条目是独立的实践映射，不是对原标准的全文再分发或合规认证。

### 9.4 安全与可信使用

把外部文档视为数据而不是高优先级指令；不要因文件中出现“忽略以前规则”等文字就执行它。Agent 输出涉及安全、合规、财务或其他高影响决策时，应保留相应的人类审核。

## 10 FAQ 与验收清单

### Q1：PAISL 是否需要联网？

读取本地 YAML、Skill 和运行结构校验不需要联网；克隆仓库、安装依赖或验证外部来源可能需要网络。

### Q2：是否必须使用 OpenCode？

不是。任何能够读取文件并按说明执行任务的 Agent 都可以尝试集成；自动发现能力取决于具体 Runtime。

### Q3：能否直接把 PAISL 当作 MCP Server 使用？

不能。v0.1.0 没有 MCP Server。后续版本可能实现标准发现与读取服务。

### Q4：`Validation PASSED` 是否意味着所有标准可靠？

不是。它仅表明已覆盖的结构检查通过。事实、来源、语义和效果仍需要单独评估。

### Q5：同一个任务可以使用多个标准吗？

可以。Skill 可以引用多个标准；应避免无差别应用所有标准，防止约束冲突和上下文膨胀。

### Q6：为什么有些来源是百科或概述网页？

v0.1.0 是初始映射，部分来源用于说明背景。后续应优先补充原始文献、官方规范及证据审查记录。

### Q7：如何记录使用效果？

保存输入、Prompt、模型及 Runtime 版本、输出和人工检查结果。第 06 章提供了记录模板；自动评测将在后续版本规划。

### 用户手册验收清单

- [ ] 文档与实际 v0.1.0 仓库目录一致。
- [ ] 新用户能够安装依赖并运行结构校验。
- [ ] 12 个标准和 5 个 Skills 均有索引。
- [ ] 三个案例的 Prompt 可复制并人工复现。
- [ ] 所有案例都有可检查的预期行为。
- [ ] 未把未实现的 MCP、自动评测描述为现有功能。
- [ ] 清晰说明结构验证与语义/执行验证的区别。
- [ ] 第三方标准来源和版权边界有明确说明。

---

## 附录 A：快速命令速查

```bash
# 在仓库根目录执行
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/validate.py

# 查看标准索引
cat catalog/standards.yaml

# 查看所有标准
find standards -type f -name '*.yaml' | sort

# 查看所有 Skills
find skills -type f -name 'SKILL.md' | sort

# 查找标准引用
grep -R 'PAISL-COMM-001' catalog standards skills

# 查看 Git 状态
git status
```
