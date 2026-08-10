# Task Breakdown — AWS Lambda Shutdown of AWS Services

## Conventions

- Each task references the relevant user story (US-xxx) and source file(s).
- **Definition of Done (DoD)** is stated per task.
- Tasks are derived from `docs-sdd/plan.md`.

## Task List

### T-001 — Define JSON Schema for configuration

- **User Story:** US-001, US-002, US-003
- **Files:** `config/schema.json`, `docs-sdd/feature.md`
- **Description:** Define a JSON Schema covering `general.schedule` (`daysOfWeek`, `times`), `general.notification.email`, and `services[]` with optional per-service `schedule`.
- **Definition of Done:** Schema validates the example config and rejects invalid values (bad day names, bad time format, missing `general`).

### T-002 — Implement configuration loader

- **User Story:** US-001
- **Files:** `src/config/loader.py`
- **Description:** Load `config.json` from the path in `CONFIG_FILE` (local package or S3).
- **Definition of Done:** Loader returns parsed dict or raises a clear error when the file is missing.

### T-003 — Implement configuration validation

- **User Story:** US-001
- **Files:** `src/config/validator.py`
- **Description:** Validate the loaded JSON against the schema; abort execution on failure.
- **Definition of Done:** Invalid config raises a typed validation error with details.

### T-004 — Implement fallback notification for invalid/missing JSON

- **User Story:** US-001
- **Files:** `src/notifier.py`, `src/handler.py`
- **Description:** On missing/invalid JSON, abort execution and send an SNS email to `FALLBACK_NOTIFICATION_EMAIL`.
- **Definition of Done:** Unit test verifies SNS publish is called with the fallback email.

### T-005 — Implement service registry and handler factory

- **User Story:** US-004
- **Files:** `src/services/registry.py`, `src/services/factory.py`
- **Description:** Map service names (`ec2`, `rds`, `ecs`, `glue-batch`, `glue-stream`, `aurora`, `batch`, `dms`) to handler classes.
- **Definition of Done:** Factory returns the correct handler for each supported service and raises for unknown services.

### T-006 — Implement EC2 handler

- **User Story:** US-004
- **Files:** `src/services/ec2_handler.py`
- **Description:** List active EC2 instances and force stop/terminate them.
- **Definition of Done:** Handler lists and shuts down all active instances; ignores already-stopped ones.

### T-007 — Implement RDS handler

- **User Story:** US-004
- **Files:** `src/services/rds_handler.py`
- **Description:** List active RDS instances and stop them.
- **Definition of Done:** Handler lists and stops all active DB instances; ignores already-stopped ones.

### T-008 — Implement ECS handler

- **User Story:** US-004
- **Files:** `src/services/ecs_handler.py`
- **Description:** List ECS services and scale them to zero (desiredCount=0).
- **Definition of Done:** Handler scales all active services to zero; ignores already-stopped ones.

### T-009 — Implement Glue handler (batch and streaming)

- **User Story:** US-004
- **Files:** `src/services/glue_handler.py`
- **Description:** List Glue jobs (batch and streaming) and stop running job runs with `glue:BatchStopJobRun`.
- **Definition of Done:** Handler stops all running job runs for both `glue-batch` and `glue-stream`; ignores already-stopped ones.

### T-010 — Implement Aurora handler

- **User Story:** US-004
- **Files:** `src/services/aurora_handler.py`
- **Description:** List Aurora DB clusters and stop them with `rds:StopDBCluster`.
- **Definition of Done:** Handler stops all active clusters; ignores already-stopped ones.

### T-011 — Implement Batch handler

- **User Story:** US-004
- **Files:** `src/services/batch_handler.py`
- **Description:** List AWS Batch running jobs and terminate them with `batch:TerminateJob`.
- **Definition of Done:** Handler terminates all running jobs; ignores completed ones.

### T-012 — Implement DMS handler

- **User Story:** US-004
- **Files:** `src/services/dms_handler.py`
- **Description:** List DMS replication tasks and instances and stop them (`dms:StopReplicationTask`, `dms:StopReplicationInstance`).
- **Definition of Done:** Handler stops all replication tasks/instances; ignores already-stopped ones.

### T-013 — Implement DMS Serverless handler

- **User Story:** US-004
- **Files:** `src/services/dms_serverless_handler.py`
- **Description:** List DMS Serverless replication configs and stop them with `dms:StopReplication`.
- **Definition of Done:** Handler stops all replication configs; ignores already-stopped ones.

### T-014 — Implement schedule matching

- **User Story:** US-002, US-003
- **Files:** `src/schedule/matcher.py`
- **Description:** Determine whether the current time/day matches a service's schedule; inherit general config when no specific schedule exists.
- **Definition of Done:** Matching logic covered by unit tests for specific, inherited, and non-matching cases.

### T-015 — Implement SNS notifier

- **User Story:** US-005
- **Files:** `src/notifier.py`
- **Description:** Publish an email to the SNS topic with service, item, failure reason, and execution time.
- **Definition of Done:** Notifier publishes to `SNS_TOPIC_ARN` with the expected subject/body.

### T-016 — Implement failure aggregation

- **User Story:** US-005
- **Files:** `src/handler.py`
- **Description:** Collect failures across services and send a single notification when failures exist; no notification when none.
- **Definition of Done:** Aggregation produces one message per run; no email when no failures.

### T-017 — Implement scheduler generation

- **User Story:** US-006
- **Files:** `src/scheduler/generator.py`
- **Description:** Create EventBridge Schedulers, one per unique time, shared by all services scheduled at that time.
- **Definition of Done:** Schedulers are created with the naming pattern `shutdown-<HHMM>`.

### T-018 — Implement scheduler idempotency

- **User Story:** US-006
- **Files:** `src/scheduler/generator.py`
- **Description:** Re-runs must not duplicate schedulers.
- **Definition of Done:** Running generation twice produces the same set of schedulers.

### T-019 — Implement scheduler cleanup

- **User Story:** US-006
- **Files:** `src/scheduler/generator.py`
- **Description:** Remove schedulers for removed configurations.
- **Definition of Done:** Removed config entries result in removed schedulers.

### T-020 — Implement scheduler enable/disable via config

- **User Story:** US-007
- **Files:** `src/config/models.py`, `src/config/schema.json`, `src/handler.py`
- **Description:** Add `enabled` (boolean, default `true`) to each service entry in the config model/schema. The Lambda skips services with `enabled: false` during shutdown. Scheduler generation is unaffected: schedulers are created per unique time from all services' effective schedules and are always **ENABLED**.
- **Definition of Done:** Setting `enabled: false` on a service makes the Lambda skip it, while scheduler creation/cleanup and their ENABLED state stay identical regardless of the `enabled` flag.

### T-021 — Write unit tests

- **User Story:** All
- **Files:** `tests/unit/`
- **Description:** pytest tests with `unittest.mock`/`moto` covering config, schedule matching, handlers, notifier, and scheduler generation.
- **Definition of Done:** All unit tests pass; high coverage of core logic.

### T-022 — Write integration tests

- **User Story:** All
- **Files:** `tests/integration/`
- **Description:** End-to-end tests with mocked AWS services (moto) exercising the full handler flow.
- **Definition of Done:** Integration tests pass in CI.

### T-023 — Write acceptance tests

- **User Story:** All
- **Files:** `tests/acceptance/`
- **Description:** Tests mapped to each acceptance criterion in `docs-sdd/feature.md`.
- **Definition of Done:** Every acceptance criterion has a passing test.

### T-024 — Structure the Terraform module

- **User Story:** All
- **Files:** `infra/versions.tf`, `infra/variables.tf`, `infra/locals.tf`, `infra/data.tf`, `infra/main.tf`, `infra/outputs.tf`, `infra/terraform.tfvars`
- **Description:** Split the Terraform module into the standard file layout. `main.tf` must contain only the main resources (Lambda function and invocation permission); auxiliary resources must live in dedicated per-service files (`infra/iam.tf`, `infra/sns.tf`, `infra/s3.tf`).
- **Definition of Done:** `terraform validate` and `terraform fmt` pass; `main.tf` contains only the main resources.

### T-025 — Package and deploy

- **User Story:** All
- **Files:** Terraform (`infra/`), `requirements.txt`
- **Description:** Provision the Lambda, IAM role, SNS topic, and scheduler generation with **Terraform**.
- **Definition of Done:** Deployment artifacts build successfully and deploy to AWS.