<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Changelog


## [Unreleased]

### Added
- `.github/CODEOWNERS`, naming the owner of every governance critical
  path
- A test that keeps the owner list complete, so a new critical
  directory cannot be added without an owner
- `docs/promotion-checklist.md`, the procedure that moves a Standard
  from `draft` to `verified`
- An evaluation case for PAISL-ENG-001, with its fixtures, so the
  security review Standard has an evaluation like the others

### Changed
- The governance records accept a `reference` field. A record that
  documents the shape of a contract records no decision, so it never
  counts as an approval, never satisfies a gate, and never goes
  stale. The evidence and bilingual reference instances use it.
- A stale bilingual review is an error for a Standard that claims to
  be verified, and a warning for one that is still in review. The
  promotion gate already refuses a stale review, so the warning
  states what the gate will decide. A review of an earlier revision
  is a warning in both cases, because it cannot authorise the content
  that came after it.
- The validator no longer warns that a verified Standard requires an
  evidence review. The promotion gate states it precisely, and it
  fails the validation when the requirement is not met.

### Documentation
- The governance document now describes the branch settings that
  complete the reviewer authorisation, and which of them a single
  maintainer can enable without blocking their own changes
- The promotion checklist states that the version moves with the
  promotion, because the digest of a record covers the whole file,
  the status line included

### Fixed
- A case whose output fixture is missing is an error. It used to be
  reported as a failed assertion, which hid an unusable case behind a
  rule that did not hold.
- A case whose input fixture is missing is an error. The missing
  input used to be replaced by an empty string, so the evaluation
  ran against nothing and the case could even pass.
- A case whose assertions were all skipped is skipped rather than
  passed. Nothing was verified, so nothing passed.
- The regular expression evaluator refuses the dangerous shapes on
  every platform, and the match itself is bounded everywhere. Where
  the platform offers a timer, the match runs under it. Where it
  does not, the match runs in a child process that can be
  terminated. A pattern that cannot be bounded at all is refused
  rather than run, because a thread is not a bound: a runaway
  regular expression keeps the lock of the interpreter.
- The check commands report a blocking finding with the exit code
  `1`, so a workflow can gate on them. The advisory findings still
  return `0`.
- The run identifier and the input digest cover the evaluation
  definitions. Two cases that read the same fixtures but assert
  different things are different evaluations.
- The evidence coverage starts from the rules of the Standards, so a
  rule that nobody linked is visible instead of invisible to the
  gate.
- An output file belongs to a single case. It used to be applied to
  every case of a suite, and a suite with an output file is now
  refused.
- The command line module no longer describes a single command, and
  the report uses the required suite when no suite is given.
- The exit code contract is stated per command and held by a test.
- A suite that names no case is refused. The counts of failures,
  errors, and skips are all zero for an empty suite, so the suite
  reported a pass without running anything.
- The three fixture problems are kept apart: a fixture that is
  missing, a fixture that leaves the repository, and a fixture that
  exists but cannot be read. The first two were already an error.
  The third ended the whole run instead of failing its own case.
- A fixture that exists and is empty is content, not a problem. It
  is evaluated as the empty text, which is what an excludes
  assertion holds for. A missing fixture is never read as an empty
  text, because that would report an unusable case as qualified.
- The declared output fixture is not required when the caller
  supplies the output.
- A case that verified nothing is not a pass. A case without any
  assertion was counted as a success, and a case whose assertions
  were all skipped could be counted as one as well. A case without an
  assertion is now refused by the command.
- The report counts the assertions beside the counts of the cases, so
  that a skipped optional assertion is visible in the summary and
  not only in the detail of a case.
- The check commands check the whole of their own domain. The
  evidence check resolves the references of the evidence records,
  the governance check resolves the references of the review records,
  the conflicts check resolves the references of the conflicts, and
  the evaluation refuses a case that names a Standard or a rule that
  does not exist. Their names promised an enforcing check, and they
  did not deliver one.
- The commands that only show a state stay out of the way. `coverage`
  and `report` never fail, so they can be used to look at the
  repository without turning it into a gate.
- The report carries the digest of the evaluation definition, of the
  suite and of every case. The regression comparison used to treat
  two results as comparable even when the assertions had changed,
  and compared results that did not describe the same evaluation.
- The documentation and the command line are held in step. The user
  guide named seven of the eight commands, and the help of the check
  commands still described them as reports. A test now holds the
  commands, the README, the user guide, and the architecture document
  together, and refuses a stage description that outlived its stage.
- The history of a review does not block the next revision of a
  Standard. A record of an earlier revision is reported and it does
  not hold a legitimate version upgrade back for ever. A record that
  belongs to the current revision still has to match it, and the
  promotion gates still ask for a record that matches the digest of
  the current content, so an approval of an earlier revision never
  authorises new content.
- The immutability of a published review record is decided by its
  content and not by the number of commits that touched it. A record
  that was edited and then restored is published again, and the
  finding goes away. The rule that counted the commits kept the
  repository broken for ever, with no way out.
- The index of the records holds every record, and only the domain of
  the command decides what is reported. A review names an evidence
  record and a gate asks for an evaluation case, both of which live in
  another domain. The commands filtered the index by domain, so the
  reference did not resolve and a complete promotion failed.


## [0.2.0] - 2026-11-22

The first release of the governance and evaluation tooling. The
evidence registry, lifecycle governance, conflict handling, and the
evaluation engine described in the v0.2.0 design documents now
exist.

### Release notes

The release adds quality governance around the Standard registry.

- Every rule can be linked to the evidence that supports it, and a
  rule only counts as supported when that evidence has been reviewed.
- A Standard cannot change status without an approved review record
  that matches its current content. Seven gates decide a promotion to
  `verified`, and six of them are checked locally.
- Rule conflicts can be declared, and the tool reports the pairs of
  rules that look alike. A candidate is a reason for a human to look,
  never a proof of a contradiction.
- Evaluation cases run deterministically and produce a report that
  holds no timestamp, no random identifier, and no absolute path.
  Two runs of the same material give the same report.
- The quality report gathers the state of the registry, the coverage,
  the evidence, the evaluation, the conflicts, and the lifecycle into
  one place, and two evaluation reports can be compared.

Reviewer authorisation is not one of the local checks. A
repository-local tool cannot establish the identity or the authority
of a reviewer, so that stays with protected branches, CODEOWNERS, and
required review rules.

### Added
- `paisl` Python package with a `src/` layout and a `pyproject.toml`
- `python -m paisl validate` command with text and JSON reports
- `python -m paisl coverage` command with text and JSON reports
- `python -m paisl evidence check` command with text and JSON reports
- `python -m paisl governance check` command with text and JSON reports
- `python -m paisl evaluate` command with text, JSON, and Markdown reports
- `python -m paisl conflicts check` command with text and JSON reports
- `python -m paisl report` command with text, JSON, and Markdown reports
- `python -m paisl compare` command for comparing two evaluation reports
- `paisl` console script entry point
- Test suite covering validator equivalence and CLI behaviour
- Data contracts for evidence records, rule evidence links,
  lifecycle reviews, semantic reviews, evaluation cases, evaluation
  suites, and conflict records
- Reference instances of the new contracts under `evidence/`,
  `governance/`, and `evaluations/`
- Four deterministic evaluators: `contains`, `excludes`, `regex`,
  and `json_path`

### Changed
- The validator implementation moved from `scripts/validate.py` into
  the `paisl` package
- `scripts/validate.py` is now a compatibility wrapper that resolves
  the package from the repository source tree
- The validator now also checks the v0.2.0 records. The v0.1.x
  baseline checks keep their behaviour and their order.
- The evidence contract now requires a reviewed record to document
  that its source was inspected.
- The review contract accepts explicit exceptions for rules that a
  reviewer accepted without reviewed evidence.
- The continuous integration workflow fetches the full history, so
  the lifecycle checks can prove that a published review record was
  not modified.
- The promotion gate for the evaluation cases now runs the evaluation
  engine instead of reporting that the engine is missing.
- The reference evaluation case checks for the action phrase rather
  than the full sentence, so it matches the wording of its fixture.
- The evaluation case contract accepts the language a case
  exercises, so that the English and the Chinese version of a rule
  can be covered by their own case.
- The semantic review contract accepts advisory suggestions from an
  automated tool. They are recorded, and they never satisfy a gate.
- The license scope check now ignores the generated report directory
  `.paisl/`, so writing a report does not make the validation fail.

### Compatibility
- `python scripts/validate.py` keeps the same output and exit codes
  and needs no installation step
- No Standard Schema changes
- The catalog version moved to 0.2.0; no standard entry changed
- No Standard or Skill content changes
- The license scope check now ignores build artefacts such as
  `*.egg-info`
- The new content directories are licensed under CC BY 4.0, matching
  the standard index
- Every Standard stays at version 0.1.0 and status `draft`. The
  release adds the tooling around them, not new rules.


## [0.1.1] - 2026-11-21

### Added
- security-review Skill for PAISL-ENG-001
- task-clarification Skill for PAISL-PROD-001
- Standard-to-Skill coverage governance

### Validation
- Validator now enforces Skill to Standard reference integrity
- Validator checks Skill structure, required sections, and frontmatter
- Validator checks Catalog metadata, category coverage, and ID numbering
- Validator checks README to Skill list consistency
- Validator checks license scope against the LICENSE-DOCS mapping

### Documentation
- Updated English and Chinese README
- Extended the user guide for seven Skills
- Documented the implemented validator capabilities in governance

### Compatibility
- No Standard Schema changes
- Catalog version synchronized to 0.1.1; no standard entries changed
- Standard index reclassified from MIT to CC BY 4.0
- No breaking changes


## [0.1.0] - 2026-11-21

### Added
- Bilingual project documentation
- Split licensing: MIT for software components, CC BY 4.0 for original
  documentation, Agent Skills, and original standard summaries
- Standard JSON Schema
- Twelve draft standard mappings
- Five Agent Skills
- Standard Catalog
- Validation script
- GitHub Actions
- Governance and contribution documentation

### Deferred
- MCP server
- Remote API
- Search service
- Automated semantic verification
