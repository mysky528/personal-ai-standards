---
name: security-review
description: >-
  Review application architecture and API designs using
  PAISL-ENG-001. Identify trust boundaries, security
  assumptions, potential risks, and verification needs.
version: 0.1.0
---

<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Security Review / 应用安全审查

## Purpose / 目的

Perform an evidence-aware preliminary security review
of an application, architecture, API, or workflow.

依据 PAISL-ENG-001，对应用、系统架构、API 或工作流
开展基于现有证据的初步安全审查。

This Skill provides guidance, not certification.

## Referenced Standards / 引用标准

- PAISL-ENG-001

Resolve this ID through `catalog/standards.yaml`
and read the corresponding standard YAML before use.

## Applicability / 适用范围

Use this Skill for:

- Application architecture reviews
- API design reviews
- Authentication and authorization design
- Data flow and trust boundary analysis
- Agent tool-access security reviews
- Preliminary security requirements analysis

Do not use it as a substitute for:

- Formal penetration testing
- Complete OWASP ASVS verification
- Regulatory compliance certification
- Production vulnerability scanning

## Input / 输入

Required:

1. System or application description
2. Components and major data flows
3. Review objective

Optional:

- Architecture diagram
- API specifications
- Authentication design
- Authorization model
- Deployment environment
- Data classification
- Existing security controls
- Threat model

Do not request secrets, credentials, private keys,
or production access tokens.

## Procedure / 执行流程

### Step 1 — Resolve the Standard

1. Read `catalog/standards.yaml`.
2. Locate `PAISL-ENG-001`.
3. Read the referenced YAML file.
4. Confirm the standard version and status.
5. Identify applicable rules and limitations.

If the standard cannot be resolved, report the
failure rather than inventing its requirements.

### Step 2 — Establish System Context

Identify:

- System purpose
- Users and external actors
- Components and services
- Data assets
- Deployment boundaries
- External integrations

Separate confirmed facts from assumptions.

### Step 3 — Identify Trust Boundaries

Examine:

- Client-to-server communication
- Service-to-service communication
- Public and private APIs
- Third-party integrations
- Database access
- Agent-to-tool interactions

Describe where data or control crosses a
trust boundary.

### Step 4 — Review Security Assumptions

Review the available evidence for:

- Identity verification
- Authentication
- Authorization
- Least privilege
- Sensitive data handling
- Input validation
- Secret management
- Audit logging
- Error handling
- Security monitoring

Mark unknown controls as "Not verified".

Never infer that a control exists merely
because it is commonly recommended.

### Step 5 — Identify Potential Risks

For each potential issue, record:

- Issue ID
- Affected component
- Observation
- Evidence or assumption
- Potential impact
- Likelihood, if supportable
- Suggested mitigation
- Verification method

Use risk levels only when sufficient context exists.

Otherwise mark the risk level as "Undetermined".

### Step 6 — Recommend Verification

Recommend specific verification activities,
such as:

- Review access-control rules
- Inspect authentication configuration
- Verify authorization at API boundaries
- Review audit logging coverage
- Check sensitive data handling
- Conduct an authorized security assessment

Do not claim these activities have been performed.

### Step 7 — Produce the Report

Use the output contract below.

## Output Contract / 输出契约

### 1. Executive Summary

- System reviewed
- Review scope
- Main observations
- Important limitations

### 2. System Context

| Component | Function | Trust Boundary |
|---|---|---|

### 3. Findings

| ID | Observation | Evidence | Risk | Action |
|---|---|---|---|---|

### 4. Unverified Assumptions

List missing evidence and questions.

### 5. Recommended Actions

Separate immediate actions from further verification.

### 6. Standards Applied

Include:

- PAISL-ENG-001
- Standard version
- Applicable rule IDs
- Standard status

### 7. Limitations

State that the report is preliminary and
does not establish OWASP ASVS compliance.

## Quality Checks / 质量检查

- [ ] The referenced standard was resolved.
- [ ] Trust boundaries were considered.
- [ ] Facts and assumptions are distinguished.
- [ ] Findings have identifiable support.
- [ ] Unknown controls are not treated as implemented.
- [ ] Recommended actions are actionable.
- [ ] No unsupported compliance claims are made.
- [ ] No credentials or secrets are exposed.

## Failure Handling / 异常处理

If the architecture is incomplete:

- Review only the known components.
- Mark unknowns explicitly.
- Request missing information when essential.

If the standard is unavailable:

- Report that the PAISL-based review cannot
  be completed as specified.
- Do not invent standard rules.

## Limitations / 局限

PAISL-ENG-001 is an independently written,
ASVS-informed practice mapping.

It is not the official OWASP ASVS specification,
an exhaustive security checklist, or certification.

A successful Skill execution does not prove
that an application is secure.