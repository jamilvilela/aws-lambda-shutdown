# Skill Specification — AWS Lambda Shutdown of AWS Services

## Purpose

Defines how the coding agent should behave when implementing this feature, including conventions, quality gates, and testing requirements.

## Behavior

- **Source of truth:** Always read `docs-sdd/feature.txt` (and `docs-sdd/feature.md`) before implementing or modifying code.
- **Consistency:** Keep all SDD documents consistent; update affected documents when requirements change.
- **Language:** All documentation and code comments in English.

## Conventions

- **Language:** Python 3.11+.
- **Type hints:** Use type hints on all public functions and methods.
- **Config models:** Use dataclasses or Pydantic models for configuration.
- **Naming:** Follow PEP 8; use descriptive names.
- **Environment variables:** All runtime configuration (paths, ARNs, emails) comes from environment variables, never hardcoded.
- **Terraform:** The module in `infra/` must follow the standard file layout (`data.tf`, `locals.tf`, `main.tf`, `outputs.tf`, `terraform.tfvars`, `variables.tf`, `versions.tf`); `main.tf` contains only the main resources, and auxiliary resources (IAM, SNS, S3) live in dedicated per-service files.

## Design Patterns (from `docs-sdd/architecture.md`)

- **Repository** for AWS service clients.
- **Strategy** for per-service shutdown logic.
- **Factory** for service handler creation.
- **Singleton** for cached configuration.
- **Dependency Injection** for testability.
- **Error handling:** try/except with structured logging and failure aggregation.

## Quality Gates

- All unit tests pass (`pytest`).
- High coverage of core logic (config, schedule matching, handlers, notifier, scheduler generation).
- No linting errors (e.g., `ruff`/`flake8`).
- Definition of Done met for each task in `docs-sdd/tasks.md`.

## Testing Requirements

- **Unit tests:** pytest with `unittest.mock` / `moto`.
- **Integration tests:** end-to-end with mocked AWS services.
- **Acceptance tests:** mapped to acceptance criteria in `docs-sdd/feature.md`.
- Run the full test suite before considering a task complete.

## Guardrails

- Do not invent requirements not present in `docs-sdd/feature.txt`; mark assumptions explicitly.
- Do not hard-code credentials or emails; use environment variables.
- Keep the Lambda within AWS timeout limits and use least-privilege IAM.