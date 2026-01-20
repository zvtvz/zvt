# Specs-Driven Workflow

This document defines how ZVT plans and delivers changes using a specs-first approach. It complements the high-level roadmap in `ZVT_STEERING_ROADMAP.md` and the reference `ZVT_PROJECT_SPECIFICATION.md`.

## Principles

- Clarity before code: write the spec before significant implementation.
- Single source of truth: keep specs up to date and code-aligned.
- Small, verifiable steps: each spec has acceptance criteria and test plan.
- Transparency: decisions and tradeoffs are documented.

## Document Types

- Change Spec (RFC): proposal for a feature/refactor/API change.
- API Spec: detailed routes, request/response, errors, versioning.
- Data Model Spec: schema fields, relationships, migrations.
- Operational Spec: deployment, observability, SLOs, runbooks.

## Spec Template (Change Spec / RFC)

- Title: concise name and scope
- Problem: what’s missing or broken; who is impacted
- Goals: what this change achieves (measurable)
- Non-Goals: out-of-scope items
- Design Overview: architecture, module changes, sequence diagrams (if any)
- API/Schema Changes: endpoints, models, migrations, compatibility
- Risks & Mitigations: data loss, downtime, perf, security
- Acceptance Criteria: testable outcomes, benchmarks
- Test Plan: unit/integration/perf tests and datasets
- Rollout Plan: flags, phases, migration/rollback
- Owners & Reviewers: accountable maintainer(s) and reviewers

Store RFCs under `docs/rfcs/YYYY-MM-<short-slug>.md`.

## Lifecycle

1) Draft
- Author creates an RFC draft and links related issues.
- Add minimal API/Data specs when applicable.

2) Review
- Submit PR; label with `rfc` and target milestone.
- At least two approvals for core subsystems; one for docs-only.
- Steering committee resolves contentious items.

3) Implement
- Break down into small PRs mapped to RFC sections.
- Keep specs updated on deviations and decisions.
- Add/extend tests to match acceptance criteria.

4) Validate
- Run unit/integration/perf tests.
- Update `CHANGELOG.md` and relevant docs.

5) Release
- Version bump if public API or data format changed.
- Provide migration notes and rollback steps.

## Versioning & Compatibility

- REST API: explicit versioning when breaking (`/api/v1`, `/api/v2`).
- Data schemas: provide DB migrations and data transformers.
- Python APIs: deprecate for ≥1 minor release before removal.

## Quality Gates

- Tests: unit and integration tests for new code paths.
- Coverage: keep or increase coverage on touched modules.
- Performance: no significant regressions on critical paths.
- Security: basic linting and dependency scanning.

## Where to Put Things

- API specs: `docs/specs/REST_API_SPEC.md` (this repo) and inline OpenAPI via FastAPI.
- Module specs: `docs/specs/MODULES_SPEC.md`.
- Project spec: `ZVT_PROJECT_SPECIFICATION.md`.
- Roadmap & governance: `ZVT_STEERING_ROADMAP.md`.

## Quick Checklist (for every change)

- Spec drafted and linked in PR
- Acceptance criteria defined and tests planned
- Backward compatibility considered and documented
- Operational impact assessed (logs, metrics, alerts)
- Docs updated (user-facing + developer)

