# Agent Definitions — AWS Lambda Shutdown of AWS Services

## Overview

This document defines the agent roles and responsibilities for implementing the feature described in `docs-sdd/feature.md`. Each agent operates within the SDD workflow and must keep all documents consistent with `docs-sdd/feature.txt`.

## Roles

### Architect

- **Responsibility:** Design the technical architecture (`docs-sdd/architecture.md`), component breakdown, data flow, and error-handling flow.
- **Inputs:** `docs-sdd/feature.md`, `docs-sdd/prd.md`
- **Outputs:** `docs-sdd/architecture.md`
- **Quality gates:** Architecture covers all user stories; naming conventions and environment variables are defined.

### Developer

- **Responsibility:** Implement the Lambda following `docs-sdd/plan.md` and `docs-sdd/tasks.md`.
- **Inputs:** `docs-sdd/architecture.md`, `docs-sdd/tasks.md`
- **Outputs:** Python source code under `src/`, unit tests under `tests/unit/`.
- **Quality gates:** Type hints, design patterns per architecture, all unit tests pass, Definition of Done met for each task.

### Tester

- **Responsibility:** Write and maintain unit, integration, and acceptance tests (`docs-sdd/tests.md`).
- **Inputs:** `docs-sdd/feature.md`, `docs-sdd/tasks.md`
- **Outputs:** Tests under `tests/`, test reports.
- **Quality gates:** Every acceptance criterion has a passing test; high coverage of core logic.

### DevOps / Deployer

- **Responsibility:** Package and deploy the Lambda, IAM role, SNS topic, and scheduler generation.
- **Inputs:** `docs-sdd/architecture.md`, `docs-sdd/plan.md`
- **Outputs:** Terraform module under `infra/` (standard file layout: `data.tf`, `locals.tf`, `main.tf`, `outputs.tf`, `terraform.tfvars`, `variables.tf`, `versions.tf`, plus per-service files `iam.tf`, `sns.tf`, `s3.tf`), CI pipeline.
- **Quality gates:** Deployment is reproducible and idempotent; `terraform validate` and `terraform fmt` pass.

## Collaboration Rules

- All agents must keep documentation consistent with `docs-sdd/feature.txt`.
- Cross-references (US-xxx, FR-xxx, NFR-xxx) must be maintained across documents.
- Assumptions not present in `docs-sdd/feature.txt` must be marked explicitly.