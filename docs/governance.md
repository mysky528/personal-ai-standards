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

Original documentation, Agent Skills, original standard summaries,
and the standard index are licensed under CC BY 4.0. Software
components are licensed under MIT. The per-directory `LICENSE` files
and the SPDX identifiers in each file are authoritative; see
`LICENSE-DOCS` in the repository root for the complete mapping.

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

### 6. Automation Status / 自动化现状

The v0.2.0 validator implements:

- Catalog to Standard referential integrity.
- Skill to Standard reference resolution.
  A Skill referencing an unknown or malformed Standard ID
  fails validation.
- Skill structure checks: frontmatter, required sections,
  and agreement with the Skill directory name.
- Catalog metadata checks: category coverage, ID numbering,
  and agreement between `catalog_version` and the release version
  declared in the CHANGELOG and both READMEs.
- README to Skill list consistency.
- License scope consistency. Every file must carry an SPDX
  identifier that matches the path to license mapping declared in
  `LICENSE-DOCS`.
- Record contract checks for the evidence, review, semantic review,
  conflict, evaluation case, and evaluation suite records.
- Referential integrity between the records. A record that names a
  Standard, rule, evidence record, or evaluation case that does not
  exist fails validation.
- Lifecycle checks: legal transitions, a status that is backed by
  an approved review record, a content digest that matches the
  reviewed file, a version update for a changed content, and a
  published review record that was not modified afterwards.
- Evidence checks: a rejected record may not support a rule, and
  contradicting evidence is surfaced for review.
- Bilingual review freshness, and a stale review of a Standard that
  left `draft`.
- Conflict checks: a confirmed or closed conflict needs a reviewer.

Not implemented:

- Semantic verification of Standard content.
- Automatic resolution of a rule conflict.
- Identity or authority of a reviewer. See the next section.

### 7. Reviewer Authorisation / 审查人授权

The tooling cannot establish who a reviewer is. A name in a YAML
file is a claim, not an identity, and no local check can turn it
into one. The `repository-authorization` gate therefore reports
`enforced externally`, and the repository has to make that true.

#### What the repository provides

`.github/CODEOWNERS` names the owner of every governance critical
path: the data contracts, the Standard registry, the governance
records, the evaluation material, the tooling, the Skills, and the
workflow. `tests/unit/test_codeowners.py` keeps that list complete.

The audit trail lives in the repository as well. A review record is
immutable once published, and it pins the digest of the content it
reviewed, so a record cannot be edited after the fact and a change
cannot inherit an old review.

#### The branch settings that complete it

Settings → Branches → Add rule for `main`:

| Setting | Recommended | Why |
|---|---|---|
| Require a pull request before merging | On | Every change gets a review trail |
| Require status checks to pass | On, using `validate` | The automated rules must pass before a merge |
| Require review for Code Owners | Off while there is one maintainer | The owner cannot approve their own pull request, so the rule would block every change |
| Require review for Code Owners | On once a second maintainer exists | The rule then means what it says |
| Dismiss stale approvals | On | An approval should not survive a later change |
| Do not allow bypassing these settings | On | The rule cannot be skipped |

A repository with a single maintainer cannot enable a required
approval, because the only possible approver is the author of the
pull request. For that reason the enforcement of the automated rules
rests on the status check, and the judgement of the maintainer
rests on the review record in `governance/reviews/`. A repository
with more than one maintainer should enable the required review and
the Code Owners review together, and should then treat the review
record as the durable copy of the decision.
