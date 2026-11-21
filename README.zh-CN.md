# 个人 AI 标准库（PAISL）

面向人类与 AI Agent 的开放、双语、机器可读标准与实践库。

[English](README.md)

**版本：** 0.1.0  
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
- `AGENTS.md`：Agent 行为契约。

## 快速开始

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate.py
```

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

原创代码采用 MIT。

原创文档、Skills 和标准摘要采用 CC BY 4.0。

第三方标准遵循原有版权与许可。

## 路线图

v0.1.0：标准仓库、Schema、Skills、CI。

v0.2.0：证据管理、规则评测、版本治理。

v0.3.0：标准检索、依赖解析、Agent 适配。

后续版本：MCP 标准服务。

## 参与贡献

参见 [CONTRIBUTING.md](CONTRIBUTING.md)。
