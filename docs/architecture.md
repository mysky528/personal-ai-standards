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

### Evaluation engine

`python -m paisl evaluate --suite core-regression` runs a suite of
cases and reports the outcome in text, JSON, or Markdown.

```bash
python -m paisl evaluate --suite core-regression
python -m paisl evaluate --case COMM-001-CASE-001 \
  --output-file .paisl/outputs/comm-001.txt
```

The engine loads a suite, loads the cases it names, resolves the
fixtures, runs the assertions, and produces the report. Only four
evaluators may run, and the evaluation contract allowlists their
names, so a case cannot select executable code.

| Evaluator | Checks |
|---|---|
| `contains` | The output contains an exact substring |
| `excludes` | The output does not contain a substring |
| `regex` | The output matches a pattern |
| `json_path` | A value inside a JSON output |

The path syntax addresses object keys and numeric array indices
separated by dots. It is not JSONPath: it has no filters, no
wildcards, and no recursive descent.

An assertion ends in `pass`, `fail`, `skip`, or `error`. An invalid
fixture, an unknown evaluator, and a failure inside the engine are
errors rather than failures. A skipped mandatory assertion never
counts as a pass, so skipping a case of a required suite fails the
suite.

#### Reproducibility

The same inputs always produce the same report. The report holds no
timestamp, no random identifier, and no absolute path. The run
identifier is derived from the content of the suite, the cases, and
the evaluated outputs, and the input digest identifies the material
that was evaluated.

#### Safety

A regular expression can match without end, so the `regex` evaluator
limits the length of a pattern and of the input, refuses constructs
that can backtrack without end, and bounds how long a single match
may run.

A report never carries the material it evaluated. It holds digests
and a short excerpt, and anything that looks like a credential is
removed from the excerpt.

### Conflicts and bilingual review

`python -m paisl conflicts check` reports the declared conflicts,
the candidates that need a human look, and the state of the bilingual
reviews.

Two kinds of conflict handling exist, and they are not the same
thing.

A **declared conflict** is a record. A person saw two rules that may
contradict each other and wrote it down. A conflict can only be
confirmed or closed once a reviewer is named, because both are human
judgements.

A **candidate** is a suggestion. The tool compares the rules of
different Standards by deterministic metadata and reports the pairs
that look alike. The signals are the action verb that opens an
instruction, the overlap of the significant English words, and the
overlap of the Chinese character pairs. A candidate is a reason to
look, never a proof: wording that resembles wording does not show
that two rules contradict each other, and the report says so
wherever it lists a candidate.

A bilingual semantic review expires on its own. The record pins the
digest of the content it reviewed, so any later change to the file
makes the review stale. A stale review of a draft Standard is a
warning; a stale review of a Standard that left draft is an error,
because a Standard beyond draft may not claim a review it no longer
has.

Suggestions from an automated tool may be recorded next to a
review, but they are advisory. They never satisfy a promotion gate
and they never stand in for the outcome of a human review.

The report also describes the bilingual evaluation coverage, which
names the rules that have an evaluation case in one language but not
in the other.

### Command line interface

```bash
python -m pip install -e ".[dev]"
python -m paisl validate
python -m paisl validate --format json
python -m paisl coverage
python -m paisl evidence check
python -m paisl governance check
python -m paisl conflicts check
python -m paisl evaluate --suite core-regression
python -m paisl report --suite core-regression
python -m paisl compare --baseline old.json --current new.json
```

#### How the outcomes are aggregated

An assertion ends in `pass`, `fail`, `skip`, or `error`. A case
aggregates them:

| The assertions of a case | The status of the case |
|---|---|
| One of them errored | `error` |
| One of them failed | `fail` |
| A mandatory one was skipped | `skip` |
| All of them were skipped | `skip` |
| There are none | `skip` |
| Otherwise | `pass` |

A case that verified nothing is not a pass. A skipped mandatory
assertion never counts as one, and a case without any assertion is
refused by the command.

A case may pass while an optional assertion was skipped, because the
mandatory assertions held. The report keeps the four case counts that
the design names, and adds the counts of the assertions beside them,
so that a skipped assertion is visible in the summary and not only
in the detail of a case.

#### Exit codes

| Code | Meaning |
|---|---|
| `0` | Success. Nothing blocking was found |
| `1` | A validation, an evaluation, or a check found something blocking |
| `2` | The arguments or the configuration are invalid |
| `3` | The tool could not complete because of an execution failure |

The contract by command:

| Command | `0` | `1` |
|---|---|---|
| `validate` | The registry, the Catalog, the Skills, and the records are valid | A finding that blocks the repository |
| `evaluate` | Every case of the suite passed | A case failed, errored, or was skipped |
| `evidence check` | No rejected record supports a rule | A rejected record supports a rule |
| `governance check` | Every Standard that claims to be verified clears the local gates | A Standard claims to be verified without clearing them |
| `conflicts check` | No confirmed conflict is still open | A confirmed conflict is still open |
| `coverage` | Always | Never. A standard without a Skill is reported, not failed |
| `report` | Always | Never. The report states what it found |
| `compare` | The two reports describe the same evaluation | They do not, so they were not compared |

A finding that is only advisory, such as a stale record of a
Standard that is still in `draft`, never changes an exit code. The
`--strict` flag of `validate` is the only way to turn a warning into
a failure.

### Compatibility

`python scripts/validate.py` keeps working unchanged. The script is
now a thin wrapper that resolves the package from the repository
source tree, so it needs no installation step and produces the same
output and exit codes as before.

The equivalence is enforced by `tests/unit/test_legacy_equivalence.py`,
which compares the current implementation against outputs recorded
from the v0.1.x validator.

### Not implemented

The evidence registry, lifecycle governance, conflict detection, and
the evaluation engine are part of the tool since v0.2.0. What the
tool still does not do:

- It cannot establish the identity or the authority of a reviewer.
  That belongs to the branch settings of the repository.
- It cannot decide whether two rules contradict each other. It
  reports candidates and leaves the judgement to a person.
- It cannot verify a source against its content. It records what a
  reviewer said about it.

The reference instances under `evidence/`, `governance/`, and
`evaluations/` document the contracts; they are not the result of an
actual review or evaluation.

## Future MCP

Potential tools:

- list_standards
- get_standard
- search_standards
- resolve_skill_standards

These are design candidates, not implemented APIs.
