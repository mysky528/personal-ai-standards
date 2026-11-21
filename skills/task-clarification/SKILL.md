---
name: task-clarification
description: >-
  Clarify goals, commitments, and next actions using
  PAISL-PROD-001. Organize actionable tasks, waiting
  items, and unresolved questions.
version: 0.1.0
---

<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Task Clarification / 任务澄清

## Purpose / 目的

Convert ambiguous commitments, goals, and task lists
into clear, actionable next steps.

依据 PAISL-PROD-001，将模糊目标、待办承诺和任务清单
整理为可执行的下一步行动。

## Referenced Standards / 引用标准

- PAISL-PROD-001

Resolve this ID through `catalog/standards.yaml`
and read the corresponding standard YAML before use.

## Applicability / 适用范围

Use this Skill for:

- Personal task clarification
- Project task breakdown
- Meeting action-item extraction
- Backlog refinement
- Weekly planning
- AI Agent task preparation

This Skill is not a full task management system.

## Input / 输入

Required:

1. Goal, task description, or unstructured task list

Optional:

- Deadlines
- Priorities
- Owners
- Dependencies
- Available resources
- Project constraints
- Existing task status

Do not invent missing deadlines, owners,
or commitments.

## Procedure / 执行流程

### Step 1 — Resolve the Standard

1. Read `catalog/standards.yaml`.
2. Locate `PAISL-PROD-001`.
3. Read the referenced YAML.
4. Confirm the standard version and status.
5. Identify applicable rules and limitations.

### Step 2 — Capture Commitments

Extract all identifiable:

- Goals
- Tasks
- Requests
- Decisions
- Waiting items
- Unresolved questions

Preserve the original intent.

Do not silently discard ambiguous items.

### Step 3 — Clarify Desired Outcomes

For each major item:

1. Identify the desired outcome.
2. Determine whether the outcome is observable.
3. Identify missing information.
4. Distinguish outcomes from actions.

If the outcome is unclear, mark it
"Needs clarification".

### Step 4 — Define Next Actions

For each actionable item:

1. Identify a concrete next step.
2. Start with an action verb.
3. Specify the object of the action.
4. Identify dependencies.
5. Identify an owner only when known.
6. Preserve any supplied deadline.

A next action should describe what to do,
not merely restate the project name.

Example:

Weak:
"Improve documentation"

Clearer:
"Review the installation section and list
commands that fail on a clean environment"

### Step 5 — Organize Tasks

Use these categories:

- Next Actions
- Projects
- Waiting For
- Needs Clarification
- Someday / Maybe

Treat these as an operational adaptation,
not an exhaustive reproduction of GTD.

### Step 6 — Identify Dependencies

Identify tasks that cannot start until:

- Information is received
- A decision is made
- Another task is completed
- An external resource becomes available

Do not invent dependencies.

### Step 7 — Prepare an Action Plan

Present:

- Immediate next actions
- Projects and desired outcomes
- Waiting items
- Clarification questions
- Known deadlines
- Suggested review points

Keep recommendations separate from user commitments.

## Output Contract / 输出契约

### 1. Goal Summary

Describe the goal and desired outcome.

### 2. Next Actions

| ID | Next Action | Owner | Deadline | Dependency |
|---|---|---|---|---|

Use "Unspecified" for unknown owners or deadlines.

### 3. Projects

| Project | Desired Outcome | Next Action |
|---|---|---|

### 4. Waiting For

| Item | Waiting On | Follow-up |
|---|---|---|

### 5. Needs Clarification

List unresolved questions.

### 6. Suggested Review

Describe when the user might review progress.
Do not create reminders unless explicitly requested.

### 7. Standards Applied

Include:

- PAISL-PROD-001
- Standard version
- Applicable rule IDs
- Standard status

## Quality Checks / 质量检查

- [ ] Original commitments are preserved.
- [ ] Outcomes and actions are distinguished.
- [ ] Next actions are concrete.
- [ ] Dependencies are identified where known.
- [ ] Missing owners and dates are not invented.
- [ ] Waiting items are separated.
- [ ] Ambiguous items remain visible.
- [ ] Suggested actions are not presented
      as user-approved commitments.

## Failure Handling / 异常处理

If the goal is unclear:

- Extract what is known.
- Mark unresolved outcomes.
- Ask focused clarification questions.

If task ownership is unknown:

- Use "Unspecified".
- Do not assume the user is the owner.

If the standard is unavailable:

- Report the unresolved standard reference.
- Do not invent PAISL requirements.

## Limitations / 局限

PAISL-PROD-001 is an independent mapping
informed by GTD concepts.

This Skill is not an official GTD implementation
or certified training resource.

It does not persist tasks, create reminders,
or update external task management systems.
