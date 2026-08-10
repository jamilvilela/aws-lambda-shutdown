---
name: sdd_generate_spec_files
description: Generate or update the full SDD (Spec-Driven Development) documentation set (feature.md, prd.md, plan.md, tasks.md, agents.md, skill.md, architecture.md, tests.md) for an AWS Lambda shutdown service, based on docs-sdd/feature.txt, with Python technical details, design patterns, best practices, and unit tests.
---

<!-- Tip: Use /create-prompt in chat to generate content with agent assistance -->

## Objective

Generate or update the complete SDD (Spec-Driven Development) documentation set for an AWS Lambda that forcibly shuts down AWS services that would otherwise run indefinitely, based on the requirements in `docs-sdd/feature.txt`.

## Source of Truth

- Read `docs-sdd/feature.txt` first. It contains the user stories (US-001 to US-006), acceptance criteria, technical acceptance criteria, and the solution flow diagram.
- Every SDD document must be consistent with this file. If requirements change, update the affected documents.

## SDD Documentation Set

Create or update the following files under `docs-sdd/`:

1. **`feature.md`** — Feature specification.
   - Feature name, summary, and scope.
   - User stories (As a... I want... So that...) with acceptance criteria and expected results.
   - Functional and non-functional requirements.
   - Traceability: each requirement mapped to its user story (US-xxx).

2. **`prd.md`** — Product Requirements Document.
   - Problem statement and goals.
   - Target users and personas.
   - Functional requirements (FR-xxx) and non-functional requirements (NFR-xxx: performance, security, cost, reliability, observability).
   - Constraints, assumptions, and dependencies (AWS Lambda, SNS, EventBridge Scheduler, S3, IAM).
   - Success metrics.

3. **`architecture.md`** — Technical architecture.
   - High-level architecture diagram (Mermaid) of the solution: EventBridge Scheduler → Lambda → AWS services → SNS.
   - Component breakdown: Lambda function, config.json, SNS topic, EventBridge Schedulers, IAM roles.
   - Data flow and error-handling flow.
   - AWS resource naming conventions and environment variables.

4. **`plan.md`** — Implementation plan.
   - Phases and milestones (e.g., Phase 1: config parsing & validation; Phase 2: service shutdown logic; Phase 3: SNS notifications; Phase 4: EventBridge Scheduler generation; Phase 5: tests & deployment).
   - Dependencies between phases and estimated effort.

5. **`tasks.md`** — Task breakdown.
   - Granular, actionable tasks derived from the plan, each referencing the relevant user story (US-xxx) and file(s).
   - Definition of Done for each task.

6. **`agents.md`** — Agent definitions.
   - Roles (e.g., architect, developer, tester) and responsibilities for implementing the feature.

7. **`skill.md`** — Skill specification.
   - How the coding agent should behave when implementing this feature (conventions, quality gates, testing requirements).

8. **`tests.md`** — Test specification.
   - Unit tests, integration tests, and acceptance tests mapped to user stories.
   - Test cases for: config parsing/validation, schedule matching (days × times list), forced shutdown of all items, SNS notification on failure, EventBridge Scheduler generation (idempotency).

## Technical Requirements

- **Language:** Python 3.11+.
- **Design patterns:** Repository pattern for AWS service clients, Strategy pattern for per-service shutdown logic, Factory for service handlers, Singleton for config, Dependency Injection for testability, and error-handling patterns (try/except with structured logging).
- **Best practices:** type hints, dataclasses/Pydantic for config models, separation of concerns, SOLID principles, environment variables for configuration, and defensive programming.
- **Unit tests:** pytest with mocks (e.g., `unittest.mock` / `moto`) covering all acceptance criteria; aim for high coverage of the core logic.

## Output Rules

- Write all SDD documentation in **English**.
- Use consistent naming and cross-references between documents (e.g., US-001, FR-001, NFR-001).
- Keep documents concise, structured with headings, tables, and diagrams (Mermaid) where useful.
- Do not invent requirements not present in `docs-sdd/feature.txt`; mark any assumptions explicitly.
