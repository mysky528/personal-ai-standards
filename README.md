<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Personal AI Standards Library (PAISL)

An open, bilingual, machine-readable library of standards
and practices for human–AI communication and collaboration.

[简体中文](README.zh-CN.md)

**Version:** 0.1.0  
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
| `.github/` | CI and contribution workflows |

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
| Software: `scripts/`, `schemas/`, `catalog/`, `.github/`, config | MIT | [`LICENSE`](LICENSE) |
| Original documentation: `docs/`, root `*.md` | CC BY 4.0 | [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0) |
| Agent Skills: `skills/` | CC BY 4.0 | [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0) |
| Original standard summaries: `standards/` | CC BY 4.0 | [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0) |

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
- v0.2.0: Evidence records, evaluation fixtures, review.
- v0.3.0: Search, dependency resolution, agent adapters.
- Later: MCP server and dynamic standard distribution.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

This is an independent project, not an official
publication of any third-party standards organization.
