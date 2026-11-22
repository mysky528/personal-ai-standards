<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 个人 AI 标准库（PAISL）

面向人类与 AI Agent 的开放、双语、机器可读标准与实践库。

[English](README.md)

**版本：** 0.2.0  
**状态：** 实验性  
**语言：** English / 简体中文  
**MCP：** 延后实现

## 项目使命

PAISL 解决两个核心问题：

1. 人类如何更准确地向 AI 表达需求。
2. 人类如何更清晰地理解、核验和使用 AI 输出。

它通过可复用的标准定义和 Agent Skills，
建立跨模型、跨工具的协作规范。

## 组成部分

- `standards/`：标准与实践定义。
- `skills/`：Agent 执行流程。
- `schemas/`：机器可读数据契约。
- `catalog/`：标准发现目录。
- `scripts/`：结构化校验。
- `docs/`：架构、治理与集成说明。
- `docs/user-guide/`：[中文用户手册](docs/user-guide/USER_GUIDE.zh-CN.md)。
- `AGENTS.md`：Agent 行为契约。


## 内置 Agent Skills

PAISL 提供七个基于文件的 Agent Skills。

| Skill | 主要用途 |
|---|---|
| standard-discovery | 标准发现与选择 |
| ste-writing | 技术文档规范化 |
| structured-thinking | 结构化思考 |
| ai-output-review | AI 输出质量审查 |
| visual-explanation | 渐进式可视化解释 |
| security-review | 应用安全初步审查 |
| task-clarification | 任务澄清与下一步行动 |

其中：

- `security-review` 引用 `PAISL-ENG-001`。
- `task-clarification` 引用 `PAISL-PROD-001`。

Standard 与 Skill 是多对多关系。

所有 Standard 必须通过 Catalog 可发现，
但不要求每个 Standard 都拥有专用 Skill。

Skill 是 Agent 执行流程，不等于第三方标准认证。

覆盖治理规则见 `docs/governance.md`。


## 快速开始

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate.py
```

也可以安装本包，从而获得完整的命令行工具：

```bash
python3 -m pip install -e ".[dev]"
python3 -m paisl --help
```

## 命令行工具

| 命令 | 用途 |
|---|---|
| `paisl validate` | 校验注册表、Catalog 与 Skills |
| `paisl coverage` | 报告已覆盖与未覆盖的部分 |
| `paisl evidence check` | 校验证据登记 |
| `paisl governance check` | 校验审查记录与晋级门禁 |
| `paisl conflicts check` | 报告已声明冲突与候选冲突 |
| `paisl evaluate --suite core-regression` | 运行确定性评测 |
| `paisl report --suite core-regression` | 生成质量报告 |
| `paisl compare --baseline FILE --current FILE` | 对比两份评测报告 |

`python scripts/validate.py` 无需先安装包即可使用，输出与退出码与旧版一致。

工具只校验**记录完整性**。它无法确立审查人的真实身份或授权，因此审查人授权仍由受保护分支、CODEOWNERS 与必需的审查规则承担。

## 使用方式

Agent 首先读取 `AGENTS.md`，选择合适的 Skill，
通过 Catalog 查找标准 ID，然后读取对应 YAML，
执行适用规则，并在必要时说明依据和限制。

## 标准生命周期

- `draft`：初稿。
- `review`：审查中。
- `verified`：完成内部来源与语义核验。
- `deprecated`：已弃用。

`verified` 不代表第三方标准机构的官方认证。

## 许可证

PAISL 采用拆分许可。

| 范围 | 许可 | 全文 |
|---|---|---|
| 软件部分：`scripts/`、`schemas/`、`.github/`、配置文件 | MIT | [`LICENSE`](LICENSE) |
| 原创文档：`docs/` 与根目录 `*.md` | CC BY 4.0 | [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0) |
| Agent Skills：`skills/` | CC BY 4.0 | [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0) |
| 原创标准摘要：`standards/` | CC BY 4.0 | [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0) |
| 标准索引：`catalog/` | CC BY 4.0 | [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0) |

每个受许可目录内含独立的 `LICENSE` 文件，每个文件以 SPDX 标识声明自身许可。

复用 CC BY 4.0 材料时必须署名并注明修改。

第三方标准遵循原有版权与许可。PAISL 摘要为独立撰写的说明，不授予其所引用标准的任何权利。

完整对应关系参见 [`LICENSE-DOCS`](LICENSE-DOCS)。

## 路线图

v0.1.0：标准仓库、Schema、Skills、CI。

v0.1.1：新增两个 Skill、引用完整性校验、覆盖治理。

v0.2.0：证据管理、规则评测、版本治理。

v0.3.0：标准检索、依赖解析、Agent 适配。

后续版本：MCP 标准服务。

## 参与贡献

参见 [CONTRIBUTING.md](CONTRIBUTING.md)。
