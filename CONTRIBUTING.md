<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Contributing to PAISL / 贡献指南

## Contributions / 贡献类型

- Standard mappings / 标准映射
- Agent Skills / Agent 技能
- Source references / 来源证据
- Evaluation examples / 评测样例
- Schema and validation improvements / 校验改进
- Bilingual translations / 双语翻译

## Required Fields / 必填字段

Every standard requires:

- Stable ID and semantic version.
- Category and kind.
- English and Chinese metadata.
- Purpose and scope.
- Identifiable sources.
- Independently written actionable rules.
- Explicit limitations.

## Workflow / 贡献流程

1. Open an issue.
2. Create a branch.
3. Add or update YAML.
4. Update the Catalog.
5. Run validation.
6. Submit a pull request.

## Review / 审查

CI validates structure, not factual authority.

Reviewers must evaluate:

- Source authenticity.
- Semantic accuracy.
- Copyright compliance.
- Bilingual consistency.
- Agent applicability.

## Licensing / 许可证

Original code contributions: MIT.

Original documentation contributions: CC BY 4.0.

The license of a new file is determined by its location and by the
SPDX identifier in its header:

- `scripts/`, `schemas/`, `catalog/`, `.github/`: MIT.
- `docs/`, `skills/`, `standards/`, and root `*.md`: CC BY 4.0.

Add `SPDX-License-Identifier: MIT` or
`SPDX-License-Identifier: CC-BY-4.0` to every new file that supports
comments, matching the license of its directory. JSON files cannot
carry inline comments and inherit the license of their directory.

Do not submit third-party material without
the necessary redistribution rights.
