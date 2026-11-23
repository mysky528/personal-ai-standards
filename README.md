<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Personal AI Standards Library (PAISL)

An open, bilingual, machine-readable library of standards
and practices for human–AI communication and collaboration.

[简体中文](README.zh-CN.md)

**Version:** 0.2.3  
**Status:** Experimental  
**Languages:** English / Simplified Chinese  
**MCP:** Deferred

## Mission

PAISL helps humans and AI agents express requirements,
understand outputs, reason systematically, verify claims,
and produce reusable knowledge artifacts.

PAISL is not merely a prompt collection.

## Components

| Directory | Responsibility |
|---|---|
| `standards/` | Versioned standard definitions |
| `skills/` | Agent execution procedures |
| `schemas/` | Machine-readable contracts |
| `catalog/` | Standard discovery registry |
| `scripts/` | Structural validation |
| `docs/` | Architecture and governance |
| `docs/user-guide/` | [User guide (Simplified Chinese)](docs/user-guide/USER_GUIDE.zh-CN.md) |
| `.github/` | CI and contribution workflows |



## Built-in Skills

PAISL includes seven file-based Agent Skills:

| Skill | Purpose | Standard IDs |
|---|---|---|
| standard-discovery | Find applicable standards | Catalog |
| ste-writing | Improve technical writing | COMM-001, COMM-003 |
| structured-thinking | Organize complex reasoning | REAS-001/002/003/004, COMM-002 |
| ai-output-review | Review AI-generated outputs | VER-001, COMM-001/002, REAS-002 |
| visual-explanation | Plan visual explanations | VIS-001, VIS-002 |
| security-review | Preliminary application security review | ENG-001 |
| task-clarification | Clarify tasks and next actions | PROD-001 |

Table entries abbreviate the standard IDs: `COMM-001` means
`PAISL-COMM-001`.

Skills are file-based procedures. Availability in a
specific Agent runtime depends on its integration method.

A Standard may exist without a dedicated Skill.

See `docs/governance.md` for coverage rules.


## Principles

1. Human-readable and machine-readable.
2. Bilingual by default.
3. Model-neutral and vendor-neutral.
4. Stable identifiers and explicit versions.
5. Evidence-aware and copyright-respecting.
6. Clear distinction between standards and practices.
7. Standards are separate from agent execution skills.

## Quick Start

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate.py
```

The package can also be installed, which adds the full command line:

```bash
python3 -m pip install -e ".[dev]"
python3 -m paisl --help
```

## Tooling

| Command | Purpose |
|---|---|
| `paisl validate` | Check the registry, the Catalog, and the Skills |
| `paisl coverage` | Report what is and is not covered |
| `paisl evidence check` | Check the evidence registry |
| `paisl governance check` | Check the review records and the promotion gates |
| `paisl conflicts check` | Report declared conflicts and candidates |
| `paisl evaluate --suite core-regression` | Run the deterministic evaluation |
| `paisl report --suite core-regression` | Write the quality report |
| `paisl compare --baseline FILE --current FILE` | Compare two evaluation reports |

`python scripts/validate.py` keeps working without an installation
step, with the same output and exit codes as before.

The tools check record integrity. They cannot establish the identity
or the authority of a reviewer, so reviewer authorisation stays with
protected branches, CODEOWNERS, and required review rules.

## Agent Integration

1. Read `AGENTS.md`.
2. Select a Skill from `skills/`.
3. Resolve referenced IDs through `catalog/standards.yaml`.
4. Read the corresponding standard YAML files.
5. Apply relevant rules.
6. Report limitations and rule references when useful.

## Standard Status

- `draft`: Initial, not substantively reviewed.
- `review`: Under substantive review.
- `verified`: Internally reviewed against sources.
- `deprecated`: Retained for compatibility.

Verification does not imply certification or endorsement
by the original standards publisher.

All v0.1.0 entries start as `draft`.

## Licensing

PAISL uses a split license.

| Scope | License | Full text |
|---|---|---|
| Software: `scripts/`, `schemas/`, `.github/`, config | MIT | [`LICENSE`](LICENSE) |
| Original documentation: `docs/`, root `*.md` | CC BY 4.0 | [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0) |
| Agent Skills: `skills/` | CC BY 4.0 | [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0) |
| Original standard summaries: `standards/` | CC BY 4.0 | [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0) |
| Standard index: `catalog/` | CC BY 4.0 | [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0) |

Each licensed directory carries its own `LICENSE` file, and each file
declares its license with an SPDX identifier.

Reusing CC BY 4.0 material requires attribution and indication of
changes.

Third-party standards retain their own licenses. A PAISL summary is
an independently written description and grants no rights to the
standard it references.

See [`LICENSE-DOCS`](LICENSE-DOCS) for the complete mapping.

## Roadmap

- v0.1.0: Registry, schema, Skills, validation, governance.
- v0.1.1: Two additional Skills, Skill reference validation, coverage governance.
- v0.2.0: Evidence records, evaluation fixtures, review.
- v0.2.1: Maintenance release, the regression matrix and the governance corrections.
- v0.2.2: Maintenance release, the regular expression evaluator answers the same on every platform.
- v0.2.3: Maintenance release, the boundaries of the evaluator, the timer of the caller, and the size of a named file.
- v0.3.0: Search, dependency resolution, agent adapters.
- Later: MCP server and dynamic standard distribution.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

This is an independent project, not an official
publication of any third-party standards organization.
