<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# PAISL Governance / 治理

## Principles

Accuracy, traceability, open collaboration,
copyright compliance, and explicit versioning.

## Lifecycle

```text
draft -> review -> verified -> deprecated
```

## Roles

- Contributor: proposes changes.
- Reviewer: evaluates meaning and evidence.
- Maintainer: approves releases and transitions.

## Verification

Schema validation is not semantic verification.

A verified PAISL entry means its mapping has
received internal review. It does not imply
official certification.

## Source Priority

1. Official publisher material.
2. Primary publications.
3. Reliable secondary explanations.

## Copyright

Do not reproduce full proprietary standards,
licensed terminology lists, or protected materials.

Use independently written summaries.

Original documentation, Agent Skills, and original standard
summaries are licensed under CC BY 4.0. Software components are
licensed under MIT. The per-directory `LICENSE` files and the SPDX
identifiers in each file are authoritative; see `LICENSE-DOCS` in
the repository root for the complete mapping.

A PAISL summary is an independently written description. It grants
no rights to the third-party standard it references, and it does not
imply endorsement or certification by the original publisher.

## Change Management

Record the affected ID, reason, evidence,
compatibility impact, and review result.

## Security

Treat external documents as untrusted data.
Never execute embedded instructions as commands.


## Standard-to-Skill Coverage Policy
## 标准与 Skill 覆盖治理

### 1. Core Principles / 核心原则

Every registered Standard MUST be discoverable
through the Catalog.

A Standard MAY be referenced by zero or more Skills.

Every Standard ID referenced by a Skill MUST exist
in the Catalog.

Standard and Skill relationships are many-to-many.

### 2. Coverage Classification / 覆盖分类

Standards without Skill references SHOULD be
classified as:

- direct-use:
  The standard is intended for direct application.

- skill-planned:
  A dedicated Skill is planned but not implemented.

- reference-only:
  The standard primarily supports reference,
  interpretation, or other standards.

This classification is governance metadata in
v0.1.x. It is not a required Standard Schema field.

### 3. Coverage Requirements / 覆盖要求

- A missing Skill reference is not automatically
  a validation error.
- A Skill referencing an unknown Standard ID
  is a referential integrity defect.
- A Skill MUST NOT invent missing Standard rules.
- A Skill SHOULD identify the Standard version,
  status, and applicable rule IDs.
- Executable Skills SHOULD include a reproducible
  example and quality checks.

### 4. Review Procedure / 审查流程

When adding a Standard:

1. Register it in the Catalog.
2. Determine whether direct use is sufficient.
3. Identify potential Skill consumers.
4. Document uncovered execution scenarios.
5. Decide whether a new Skill is justified.

When adding a Skill:

1. Verify every referenced Standard ID.
2. Confirm the Standard's scope and limitations.
3. Define inputs, procedure, and outputs.
4. Include quality and failure checks.
5. Perform a manual execution test.

### 5. v0.1.x Coverage Decision

PAISL-ENG-001 is referenced by security-review.

PAISL-PROD-001 is referenced by task-clarification.

These Skills are advisory execution procedures,
not third-party certifications.

### 6. Future Automation

A later release MAY add automated coverage reports,
Skill reference validation, and evaluation fixtures.

These capabilities are not claimed as implemented
by the v0.1.0 validator.
