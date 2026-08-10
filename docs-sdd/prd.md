# Product Requirements Document (PRD) — AWS Lambda Shutdown of AWS Services

## Problem Statement

AWS services such as EC2 instances, RDS/Aurora databases, ECS services, Glue jobs, AWS Batch jobs, and DMS replication tasks can be left running indefinitely, generating unnecessary cost and security exposure. There is no automated, configurable mechanism to forcibly shut down these resources on a schedule.

## Goals

- Provide a single, configuration-driven Lambda that forcibly shuts down AWS services that run indefinitely.
- Allow administrators to define which services to scan and when, without changing code.
- Notify administrators by email (via SNS) when a resource cannot be shut down or an error occurs.
- Automatically schedule the Lambda execution through EventBridge Schedulers derived from the configuration.

## Non-Goals

- Starting or restarting services.
- Manual trigger UI.
- Multi-account / multi-region orchestration.

## Target Users and Personas

| Persona | Description | Needs |
|---------|-------------|-------|
| **AWS Infrastructure Administrator** | Responsible for managing AWS resources and controlling cloud costs. | Configure services and schedules via JSON; receive failure notifications; ensure no resource runs indefinitely. |

## Functional Requirements

| ID | Requirement | Traceability |
|----|-------------|--------------|
| FR-01 | Read and parse the JSON configuration file at the start of each execution. | US-001 |
| FR-02 | Shut down only the services listed in the JSON. | US-001 |
| FR-03 | Interrupt execution and notify via SNS when the JSON is missing or invalid. | US-001 |
| FR-04 | Provide default `daysOfWeek` and `times` in `general.schedule`. | US-002 |
| FR-05 | Inherit the general configuration when a service has no `schedule`. | US-002, US-003 |
| FR-06 | Override the general configuration with a service-specific `schedule`. | US-003 |
| FR-07 | List all active items of each configured service. | US-004 |
| FR-08 | Forcibly shut down all active items (force stop/terminate). | US-004 |
| FR-09 | Ignore items already shut down without error. | US-004 |
| FR-10 | Send an SNS email when an item is not shut down or an error occurs. | US-005 |
| FR-11 | Include service, item, failure reason, and execution time in the email. | US-005 |
| FR-12 | Do not send email when there are no failures. | US-005 |
| FR-13 | Generate EventBridge Schedulers from the configuration (one per unique time). | US-006 |
| FR-14 | Make scheduler generation idempotent. | US-006 |
| FR-15 | Remove schedulers of removed configurations. | US-006 |
| FR-16 | Provide an `enabled` key (boolean, default `true`) per service in the `services` list to enable/disable its shutdown. | US-007 |
| FR-17 | Skip services with `enabled: false` during shutdown; the `enabled` flag must not affect EventBridge Scheduler generation. | US-007 |

## Non-Functional Requirements

| ID | Requirement | Category |
|----|-------------|----------|
| NFR-01 | Complete within the AWS Lambda timeout (default 15 minutes). | Performance |
| NFR-02 | Use least-privilege IAM permissions. | Security |
| NFR-03 | Emit structured logs (service, item, result, errors). | Observability |
| NFR-04 | Minimize cost by avoiding idle running resources. | Cost |
| NFR-05 | Handle partial failures gracefully and continue with remaining items. | Reliability |
| NFR-06 | Validate the configuration against a JSON Schema before execution. | Reliability |
| NFR-07 | Support Python 3.11+ runtime. | Maintainability |

## Constraints, Assumptions, and Dependencies

### Constraints

- Runs as a single AWS Lambda function.
- Configuration is provided as a JSON file (`config.json`).
- Notifications are sent through a single AWS SNS topic.
- Infrastructure must be provisioned with **Terraform** (no CloudFormation or other IaC framework).
- The Terraform module must follow a standard file layout (`data.tf`, `locals.tf`, `main.tf`, `outputs.tf`, `terraform.tfvars`, `variables.tf`, `versions.tf`); `main.tf` must contain only the main resources, and auxiliary resources (IAM, SNS, S3) must live in dedicated per-service files.

### Assumptions

- Single AWS account and single region.
- The fallback notification email (`jamilvilela@gmail.com`) is configured via the `FALLBACK_NOTIFICATION_EMAIL` environment variable.
- Supported services (configured in `config.json`): EC2, RDS, ECS, Glue Batch, Glue Streaming, Aurora, AWS Batch, DMS, DMS Serverless (extensible via a service registry).

### Dependencies

- AWS Lambda
- AWS SNS
- AWS EventBridge Scheduler
- AWS S3 (optional, for hosting `config.json`)
- AWS IAM
- Terraform (Infrastructure as Code)

## Success Metrics

| Metric | Target |
|--------|--------|
| Percentage of configured items shut down per run | 100% |
| Notification delivery on failure | 100% of failure events |
| Scheduler generation idempotency (no duplicates on re-run) | 100% |
| Configuration validation failures caught before execution | 100% |