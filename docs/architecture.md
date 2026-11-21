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
are not part of the tool yet. No command exposes them.

## Future MCP

Potential tools:

- list_standards
- get_standard
- search_standards
- resolve_skill_standards

These are design candidates, not implemented APIs.
