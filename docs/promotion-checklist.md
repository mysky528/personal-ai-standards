# Promoting a Standard / 标准晋级清单

This is the procedure for moving a Standard from `draft` to
`verified`. It is written for a repository with one maintainer, and
it assumes the tooling of the v0.2.0 release.

The procedure does not change the meaning of a Standard. It records
the decisions that a person made, so that the state of the repository
can be checked later.

## The seven gates

`python -m paisl governance check --all` reports the gates of every
Standard. A Standard may only reach `verified` when the first six
are satisfied.

| Gate | Checked by the tooling |
|---|---|
| `valid-standard-yaml` | Yes |
| `current-bilingual-review` | Yes |
| `reviewed-evidence-coverage` | Yes |
| `no-blocking-conflicts` | Yes |
| `mandatory-evaluation-cases` | Yes |
| `approved-review-record` | Yes |
| `repository-authorization` | No. It lives in the branch settings |

## The order of work

The digest of a record pins the exact bytes of the Standard file it
reviewed. A record therefore has to be written against the file as
it will be after the promotion, which means the status change comes
first and the records follow it in the same change.

1. Review the evidence.
2. Link the evidence to the rules.
3. Run the evaluation.
4. Change the status of the Standard.
5. Write the records that pin the new digest.
6. Obtain the authorisation.
7. Verify.

Steps 1 to 3 do not touch the Standard file, so the digest of the
file is stable while they happen.

## Step 1 — Review the evidence

A source is registered first and verified later. Registering a URL
is not a review: the record has to say that the source was actually
inspected.

Read the source, then write a record in `evidence/records/`:

```yaml
# SPDX-License-Identifier: CC-BY-4.0
id: EVD-0002
schema_version: "0.2.0"
title: "The title of the source"
source:
  url: "https://example.org/the-source"
  type: official          # official, primary, or secondary
  publisher: "The publisher"
  retrieved_at: "2026-11-22T00:00:00Z"
  accessed: true
review:
  status: reviewed        # unreviewed, reviewed, or rejected
  reviewed_by: "The reviewer"
  reviewed_at: "2026-11-22T00:00:00Z"
  rationale: "What the reviewer checked and what was found."
notes: null
```

The schema refuses a `reviewed` record that does not document the
inspection, so `accessed`, `retrieved_at`, the reviewer, the time,
and the rationale are all required.

## Step 2 — Link the evidence to the rules

A rule is covered by the evidence that supports it. Write
`evidence/links/<standard_id>.yaml`:

```yaml
# SPDX-License-Identifier: CC-BY-4.0
schema_version: "0.2.0"
standard_id: PAISL-ENG-001
standard_version: "0.2.0"
rules:
  - rule_id: R001
    evidence:
      - evidence_id: EVD-0002
        relationship: supports   # supports, context, or contradicts
        locator: "The section or requirement that backs the rule"
        note: null
```

`context` explains a rule without backing it, and `contradicts`
raises a conflict. Only `supports` counts towards the coverage of a
rule.

## Step 3 — Run the evaluation

The cases of the Standard must pass.

```bash
python -m paisl evaluate --suite core-regression
```

A Standard without a case has no evaluation, and the gate
`mandatory-evaluation-cases` stays unsatisfied. A new case belongs
in `evaluations/cases/`, its fixtures in `evaluations/fixtures/`, and
the suite has to name it.

## Step 4 — Change the status and the version

Edit the Standard file. The status moves to `verified`, and the
version moves with it.

```yaml
version: 0.2.0
status: verified
```

The version moves because the digest of a record covers the whole
file, the status line included. A record that reviewed the earlier
revision therefore no longer matches, and the rule that refuses a
change without a version update would hold the Standard back. Moving
the version separates the two revisions: the earlier records belong
to the earlier revision, and the new records belong to the new one.

A change to the rules themselves always needs a version update, and
the validator refuses a change without one.

Compute the digest of the file **after** this edit:

```bash
shasum -a 256 standards/engineering/owasp-asvs.yaml
```

## Step 5 — Write the records that pin the new digest

Two records, both pinning the digest from step 4.

The bilingual review, in `governance/reviews/`:

```yaml
# SPDX-License-Identifier: CC-BY-4.0
id: SEM-0002
schema_version: "0.2.0"
standard_id: PAISL-ENG-001
standard_version: "0.2.0"
reviewed_content_sha256: "<the digest from step 4>"
languages:
  - en
  - zh-CN
reviewer: "The reviewer"
reviewed_at: "2026-11-22T00:00:00Z"
outcome: pass              # pass, fail, or needs_work
summary:
  en: "What the reviewer checked."
  zh-CN: "审查者检查了什么。"
findings: []
```

The lifecycle review, in `governance/reviews/`:

```yaml
# SPDX-License-Identifier: CC-BY-4.0
id: REV-0002
schema_version: "0.2.0"
standard_id: PAISL-ENG-001
standard_version: "0.2.0"
from_status: review
to_status: verified
reviewed_content_sha256: "<the digest from step 4>"
reviewer: "The reviewer"
reviewed_at: "2026-11-22T00:00:00Z"
decision: approved         # approved or rejected
rationale: "Why the Standard may be verified."
evidence_ids:
  - EVD-0002
```

Commit the status change and both records together. A record that
is published is never edited again; a correction is a new record.

## Step 6 — Obtain the authorisation

The tooling cannot establish who a reviewer is. The authorisation
belongs to the branch settings of the repository: the pull request
has to be merged by someone the repository trusts, and the rules
that apply are described in `docs/governance.md`.

## Step 7 — Verify

```bash
python scripts/validate.py
python -m paisl governance check --all
python -m paisl evaluate --suite core-regression
```

The first must report no errors, the second must show every gate of
the Standard satisfied apart from the external one, and the third
must pass.

## The illustrative records in the repository

The repository holds one illustrative lifecycle review, `REV-0001`,
that was published before the contracts knew about the `reference`
field. A published review record is immutable, so it cannot be
corrected in place. It records no decision, it satisfies no gate,
and after the content moves on the tooling reports it as stale, which
is the truth. A new illustrative record would carry the field from
the start.

## What must not be done

- Do not edit a published review record. Write a new one.
- Do not copy the templates without checking the source. A record
  that says a source was inspected when nobody read it is worse than
  no record at all.
- Do not set `status: verified` and hope the gates pass. The
  validator refuses a Standard that claims to be verified without
  the records that back it.
- Do not promote a Standard because a candidate conflict was
  dismissed. A candidate needs a human decision, recorded as a
  conflict record with a reviewer.
