<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Agent Integration / Agent 集成

## v0.1.0

PAISL uses file-based integration.

No MCP server is provided.

## Workflow

1. Give the agent access to the PAISL repository.
2. Read `AGENTS.md`.
3. Select a Skill.
4. Resolve referenced standard IDs.
5. Read the corresponding YAML definitions.
6. Apply relevant rules.
7. Report important limitations.

## Example

```text
Use PAISL to improve this technical explanation.

Read:
- skills/ste-writing/SKILL.md
- PAISL-COMM-001
- PAISL-COMM-003

Preserve technical meaning.
Do not claim ASD-STE100 certification.
```

## Compatibility

Skill discovery and installation depend on the
agent runtime.

OpenCode, Codex, Claude Code, and other agents
may require different configuration or adapters.

Do not assume automatic cross-platform discovery.

## Future MCP

A later MCP service may expose standard discovery,
retrieval, and dependency resolution.

The Git repository remains the source of truth.
