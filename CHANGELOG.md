<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Changelog


## [Unreleased]

### Added
- `.github/CODEOWNERS`, naming the owner of every governance critical
  path
- A test that keeps the owner list complete, so a new critical
  directory cannot be added without an owner

### Documentation
- The governance document now describes the branch settings that
  complete the reviewer authorisation, and which of them a single
  maintainer can enable without blocking their own changes


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
