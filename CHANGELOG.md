<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Changelog


## [Unreleased]

Work in progress towards v0.2.0. Only the items below exist; the
evidence registry, lifecycle governance, conflict detection, and
evaluation engine described in the v0.2.0 design documents are not
implemented yet.

### Added
- `paisl` Python package with a `src/` layout and a `pyproject.toml`
- `python -m paisl validate` command with text and JSON reports
- `paisl` console script entry point
- Test suite covering validator equivalence and CLI behaviour

### Changed
- The validator implementation moved from `scripts/validate.py` into
  the `paisl` package
- `scripts/validate.py` is now a compatibility wrapper that resolves
  the package from the repository source tree

### Compatibility
- `python scripts/validate.py` keeps the same output and exit codes
  and needs no installation step
- No Standard Schema changes
- No Catalog changes
- No Standard or Skill content changes
- The license scope check now ignores build artefacts such as
  `*.egg-info`


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
