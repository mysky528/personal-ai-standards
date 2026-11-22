<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# PAISL Architecture / 架构

## Layers

```text
Human / AI Agent
       |
       v
  Agent Instructions
       |
       v
      Skills
       |
       v
 Standards Registry
       |
       +-- YAML Definitions
       +-- Catalog
       +-- JSON Schema
       +-- Validation
```

## Standards

Versioned YAML records define reusable guidance,
source references, rules, and limitations.

## Skills

Skills describe how agents execute tasks using
one or more referenced standards.

## Catalog

The Catalog maps stable standard IDs to files.

## Validation

CI checks structural integrity and registry consistency.

Structural validation does not establish
factual accuracy or official compliance.

## Versioning

Repository releases and individual standard versions
are maintained separately.

## Tooling (v0.2.0, in development)

The v0.2.0 development branch moves the validator into an
installable package and adds governance and evaluation services
around it.

```text
standards/  catalog/  schemas/  skills/
       |
       v
   paisl package  (src/paisl/)
       |
       +-- registry        Catalog and Standard resolution
       +-- schema_validation  JSON Schema checks
       +-- coverage        Skill reference integrity
       +-- licensing       Path to license scope
       +-- evidence        Evidence registry        (planned)
       +-- lifecycle       Lifecycle governance     (planned)
       +-- conflicts       Conflict detection       (planned)
       +-- evaluation      Evaluation engine        (planned)
       +-- reporting       Report rendering
       +-- cli             Command line interface
```

### Data contracts (v0.2.0, in development)

The v0.2.0 contracts live beside the Standard schema in `schemas/`.

| Contract | Schema | Holds |
|---|---|---|
| Evidence record | `evidence.schema.json` | A registered source and its review state |
| Rule evidence link | `rule-evidence.schema.json` | The links between rules and evidence |
| Lifecycle review | `review.schema.json` | A decision on a status transition |
| Semantic review | `semantic-review.schema.json` | A bilingual content review |
| Evaluation case | `evaluation-case.schema.json` | Assertions about an output |
| Evaluation suite | `evaluation-suite.schema.json` | A named group of cases |
| Conflict record | `conflict.schema.json` | A declared or suspected rule overlap |

Lifecycle review and semantic review are separate contracts on
purpose. A lifecycle review answers "may this Standard change
status", while a semantic review answers "is the bilingual content
still correct". They expire independently, and a Standard may hold
a current lifecycle review while its semantic review is stale.

The contracts constrain the shape of a record. Whether a referenced
Standard, rule, evidence record, or evaluation case exists is a
referential integrity question that the validator answers.

### Additional checks (v0.2.0)

The v0.2.0 validator extends the v0.1.x baseline. The baseline
checks keep their behaviour and their order, so a repository that
passed before still passes. The following checks are new, and they
report only when a record is wrong:

- every governance and evaluation record is validated against its
  contract
- a record that refers to a Standard, rule, evidence record, or
  evaluation case that does not exist is reported
- an evaluation case whose fixture points outside the repository, or
  at a file that is missing, is reported
- a record in a known directory with an unknown identifier prefix is
  reported
- a rejected evidence record that supports a rule is reported
- evidence that contradicts a rule is surfaced for review

`python scripts/validate.py` and `python -m paisl validate` run the
same checks. The compatibility wrapper keeps the v0.1.x command
contract, including its output format.

### Evidence registry

`python -m paisl evidence check` reports how well the rules of each
Standard are supported.

A rule is supported when an evidence record with the `supports`
relationship is linked to it. A rule is *sufficient for verification*
only when at least one of those records has been reviewed. A `context`
relationship never satisfies the requirement, because it explains the
rule without backing it.

A reviewed record must name a reviewer, a time, and a rationale, and
must record that the source was inspected. A URL alone is never
reviewed evidence. These rules are part of the evidence contract, so
the schema rejects a record that breaks them.

### Coverage report

`python -m paisl coverage` describes how completely the repository is
covered. It reports standards without a Skill reference, without
evidence links, without evaluation cases, without a lifecycle
review, or without a semantic review, together with the skills that
refer to no standard, the evidence records that no rule links, and
the conflicts that block a promotion.

A standard without a Skill reference is reported, never failed. A
standard may be intended for direct use, and the coverage policy
says that a missing reference is not automatically an error.

### Lifecycle governance

`python -m paisl governance check` reports the state of the
lifecycle and the gates that a promotion has to clear.

A Standard may only move along the transitions below.

| From | To | Meaning |
|---|---|---|
| `draft` | `review` | The Standard enters review |
| `review` | `draft` | The review sent it back |
| `review` | `verified` | The Standard was verified |
| `verified` | `review` | The verification no longer holds |
| `verified` | `deprecated` | The Standard was retired |
| `deprecated` | `draft` | The Standard was reactivated |

`deprecated` to `draft` is a deliberate reactivation and needs a new
review trail.

Every status change is checked against the review records. A
Standard that left `draft` must have an approved record, and that
record must match the current content of the file. A change to the
content of a Standard invalidates the digest of the record that
reviewed it, so a modification never inherits a verification. A
substantive change also requires a version update.

A published review record must not be modified. The check reads the
history of the file, so it needs a full clone; the continuous
integration workflow fetches one.

### Promotion gates

A promotion from `review` to `verified` has to clear seven gates.

| Gate | Checked locally |
|---|---|
| `valid-standard-yaml` | Yes |
| `current-bilingual-review` | Yes |
| `reviewed-evidence-coverage` | Yes |
| `no-blocking-conflicts` | Yes |
| `mandatory-evaluation-cases` | Once the evaluation engine exists |
| `approved-review-record` | Yes |
| `repository-authorization` | No, enforced outside the repository |

The last gate is the important boundary. A repository-local CLI
cannot establish the real identity or the authority of a reviewer
from a YAML string. Reviewer authorization is enforced by protected
Git branches, CODEOWNERS, and required GitHub review rules. The local
checks establish record integrity, never identity authenticity, and
the report says so rather than claiming a check it cannot make.

### Command line interface

Only the `validate` command exists so far.

```bash
python -m pip install -e ".[dev]"
python -m paisl validate
python -m paisl validate --format json
```

Exit codes: `0` success, `1` validation failure, `2` invalid
arguments, `3` execution error.

### Compatibility

`python scripts/validate.py` keeps working unchanged. The script is
now a thin wrapper that resolves the package from the repository
source tree, so it needs no installation step and produces the same
output and exit codes as before.

The equivalence is enforced by `tests/unit/test_legacy_equivalence.py`,
which compares the current implementation against outputs recorded
from the v0.1.x validator.

### Not implemented yet

The evidence registry, lifecycle governance, conflict detection, and
evaluation engine are described in the v0.2.0 design documents and
are not part of the tool yet. No command exposes them. The
reference instances under `evidence/`, `governance/`, and
`evaluations/` document the contracts; they are not the result of an
actual review or evaluation.

## Future MCP

Potential tools:

- list_standards
- get_standard
- search_standards
- resolve_skill_standards

These are design candidates, not implemented APIs.
