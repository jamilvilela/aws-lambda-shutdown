# Feature Specification — AWS Lambda Shutdown of AWS Services

## Feature Overview

| Field | Value |
|-------|-------|
| **Feature ID** | FEAT-SHUTDOWN |
| **Name** | AWS Lambda Shutdown of AWS Services |
| **Status** | Draft |
| **Source of Truth** | `docs-sdd/feature.txt` |

## Summary

An **AWS Lambda** that forcibly shuts down AWS services that would otherwise run indefinitely. The Lambda reads a **JSON configuration file** that defines:

- Which services should be scanned;
- The times and days of the week for each service;
- The general configuration (default days/times and notification email);
- The automatic generation of the **EventBridge Schedulers** that trigger the Lambda.

If any service item is not shut down or an error occurs, an email is sent via **AWS SNS** to the email configured in the general section of the JSON.

## Scope

### In Scope

- Reading and validating the JSON configuration file.
- Forced shutdown of all items of each configured service.
- SNS email notification when an item is not shut down or an error occurs.
- Automatic generation of EventBridge Schedulers from the configuration.

### Out of Scope

- Starting or restarting services.
- Manual trigger UI or web console.
- Multi-account / multi-region orchestration (single account and region assumed).

### Constraints

- Infrastructure must be provisioned with **Terraform** (no CloudFormation or other IaC framework).
- The Terraform module must follow a standard file layout (`data.tf`, `locals.tf`, `main.tf`, `outputs.tf`, `terraform.tfvars`, `variables.tf`, `versions.tf`); `main.tf` must contain only the main resources, and auxiliary resources (IAM, SNS, S3) must live in dedicated per-service files.

## User Stories

### US-001 — Configure services via JSON file

**As** an AWS infrastructure administrator,
**I want** to configure in a JSON file the list of services to be scanned by the Lambda,
**So that** I can control which services will be shut down without changing the Lambda code.

**Acceptance criteria:**
- The JSON file must contain a list of services to be scanned.
- The Lambda must read the JSON file at the start of each execution.
- Only the services listed in the JSON must be shut down.
- If the JSON file is missing or invalid, the execution must be interrupted and an error notification must be sent via SNS to the email **jamilvilela@gmail.com**.
- Since the JSON may be missing/invalid, the fallback email must be configured outside the JSON (e.g., environment variable `FALLBACK_NOTIFICATION_EMAIL`).

**Expected result:** The Lambda shuts down only the services listed in the JSON file.

### US-002 — General configuration of times and days of the week

**As** an AWS infrastructure administrator,
**I want** to define the default times and days of the week in the general section of the JSON file,
**So that** services without a specific configuration are shut down at those times.

**Acceptance criteria:**
- The `general.schedule` section must contain default `daysOfWeek` and `times` (list of times).
- The `general.notification.email` section must contain the notification email.
- Services without their own `schedule` must use the general configuration.
- The general configuration is mandatory; without it, the JSON must be considered invalid.

**Expected result:** All services without a specific configuration are shut down at the times and days of the week defined in the general configuration.

### US-003 — Per-service specific configuration

**As** an AWS infrastructure administrator,
**I want** to define specific times and days of the week for each service,
**So that** each service can be shut down at different times.

**Acceptance criteria:**
- Each item in the `services` list can have its own `schedule` with `daysOfWeek` and `times` (list of times).
- The service-specific configuration must override the general configuration.
- If the service has no `schedule`, it must use the general configuration.
- The JSON must be rejected if it contains invalid fields or values outside the expected pattern.

**Expected result:** Each service is shut down according to its specific configuration or, in its absence, according to the general configuration.

### US-004 — Forced shutdown of all service items

**As** an AWS infrastructure administrator,
**I want** the Lambda to forcibly shut down all items of each configured service,
**So that** no resource keeps running indefinitely.

**Acceptance criteria:**
- The Lambda must list all active items of each configured service.
- All found items must be forcibly shut down (force stop/terminate).
- Items already shut down must be ignored, without generating an error.
- The shutdown must be applied to all items, without exception.

**Expected result:** All items of each configured service are forcibly shut down.

### US-005 — Email notification on failure

**As** an AWS infrastructure administrator,
**I want** to receive an email via AWS SNS when an item is not shut down or an error occurs,
**So that** I can act quickly on resources that were not shut down.

**Acceptance criteria:**
- The email must be sent via AWS SNS to the email configured in `general.notification.email`.
- The email must be sent when a service item is not shut down.
- The email must be sent when an error occurs during execution.
- The email must contain details: service, item, failure reason, and execution time.
- If there are no failures, no email must be sent.

**Expected result:** The administrator receives an email with the details of each failure or item not shut down.

### US-006 — Automatic EventBridge Scheduler generation

**As** an AWS infrastructure administrator,
**I want** the JSON file configuration to automatically generate the EventBridge Schedulers,
**So that** the Lambda runs automatically at the configured times and days.

**Acceptance criteria:**
- A scheduler must be created for each unique time in the effective schedules (shared by all services scheduled at that time).
- The scheduler must trigger the Lambda at each time and on the configured days.
- The generation must be idempotent: re-runs must not duplicate schedulers.
- Schedulers of removed configurations must be removed.

**Expected result:** The Lambda runs automatically according to the times and days defined in the JSON file.

### US-007 — Enable/disable individual services via config

**As** an AWS infrastructure administrator,
**I want** to enable or disable each service through an `enabled` key on each service entry in `config.json`,
**So that** I can pause shutdowns for specific services without removing them from the config.

**Acceptance criteria:**
- Each service entry may have an `enabled` key that must be a boolean (default `true`).
- When `false`, the service must be skipped by the Lambda: its items are never shut down.
- EventBridge Schedulers are generated per unique day/time from the effective schedules of **all** services and are always **ENABLED**; the `enabled` flag must not disable, enable, delete, or create any scheduler.
- Re-running the generation with a changed `enabled` flag must not alter the set of schedulers.

**Expected result:** Setting `enabled: false` on a service prevents the Lambda from shutting it down, while its schedule remains unchanged and its scheduler stays ENABLED in the EventBridge Scheduler console.

## Functional Requirements

| ID | Requirement | Traceability |
|----|-------------|--------------|
| FR-001 | The Lambda must read and parse the JSON configuration file at the start of each execution. | US-001 |
| FR-002 | Only the services listed in the JSON must be shut down. | US-001 |
| FR-003 | If the JSON is missing or invalid, execution must be interrupted and an error notification sent via SNS to the fallback email. | US-001 |
| FR-004 | The `general.schedule` section must provide default `daysOfWeek` and `times`. | US-002 |
| FR-005 | Services without their own `schedule` must inherit the general configuration. | US-002, US-003 |
| FR-006 | A service-specific `schedule` must override the general configuration. | US-003 |
| FR-007 | The Lambda must list all active items of each configured service. | US-004 |
| FR-008 | All active items must be forcibly shut down (force stop/terminate). | US-004 |
| FR-009 | Items already shut down must be ignored without error. | US-004 |
| FR-010 | An email must be sent via SNS when an item is not shut down or an error occurs. | US-005 |
| FR-011 | The notification email must contain service, item, failure reason, and execution time. | US-005 |
| FR-012 | No email must be sent when there are no failures. | US-005 |
| FR-013 | EventBridge Schedulers must be generated from the configuration (one per unique time). | US-006 |
| FR-014 | Scheduler generation must be idempotent. | US-006 |
| FR-015 | Schedulers of removed configurations must be removed. | US-006 |
| FR-016 | Each service entry may have an `enabled` key (boolean, default `true`) to enable/disable its shutdown. | US-007 |
| FR-017 | The Lambda must skip services with `enabled: false`; the `enabled` flag must not affect EventBridge Scheduler generation. | US-007 |

## Non-Functional Requirements

| ID | Requirement | Category |
|----|-------------|----------|
| NFR-01 | The Lambda must complete within the AWS Lambda timeout (default 15 minutes). | Performance |
| NFR-02 | The Lambda must use least-privilege IAM permissions. | Security |
| NFR-03 | The Lambda must log structured output (service, item, status, errors). | Observability |
| NFR-04 | The solution must minimize cost (no idle resources left running). | Cost |
| NFR-05 | The Lambda must handle partial failures gracefully and continue processing remaining items. | Reliability |
| NFR-06 | The configuration must be validated against a JSON Schema before execution. | Reliability |

## Supported Services

The following services are supported and currently configured in `config.json`:

| Service | AWS Resource | Shutdown Action | IAM Permissions |
|---------|--------------|-----------------|-----------------|
| `ec2` | EC2 Instances | Force stop instances | `ec2:DescribeInstances`, `ec2:StopInstances`, `ec2:TerminateInstances` |
| `rds` | RDS DB Instances | Stop DB instances | `rds:DescribeDBInstances`, `rds:StopDBInstance` |
| `ecs` | ECS Services | Scale to zero (desiredCount=0) | `ecs:ListServices`, `ecs:DescribeServices`, `ecs:UpdateService` |
| `glue-batch` | Glue Jobs (ETL batch) | Stop running job runs | `glue:GetJobs`, `glue:GetJobRuns`, `glue:BatchStopJobRun` |
| `glue-stream` | Glue Streaming Jobs | Stop running job runs | `glue:GetJobs`, `glue:GetJobRuns`, `glue:BatchStopJobRun` |
| `aurora` | Aurora DB Clusters | Stop DB clusters | `rds:DescribeDBClusters`, `rds:StopDBCluster` |
| `batch` | AWS Batch Jobs | Terminate running jobs | `batch:DescribeJobs`, `batch:CancelJob`, `batch:TerminateJob` |
| `dms` | DMS Replication Tasks / Instances | Stop replication tasks and instances | `dms:DescribeReplicationTasks`, `dms:DescribeReplicationInstances`, `dms:StopReplicationTask`, `dms:StopReplicationInstance` |
| `dms-serverless` | DMS Serverless Replication Configs | Stop replication configs | `dms:DescribeReplicationConfigs`, `dms:StopReplication` |

## Configuration Example

```json
{
  "general": {
    "schedule": {
      "daysOfWeek": ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"],
      "times": ["03:00", "06:00", "22:00", "23:59"]
    },
    "notification": {
      "email": "jamilvilela@gmail.com"
    }
  },
  "services": [
    { "name": "ec2", "enabled": true },
    { "name": "rds", "enabled": true },
    { "name": "ecs", "enabled": true },
    { "name": "glue-batch", "enabled": true },
    { "name": "glue-stream", "enabled": true },
    { "name": "aurora", "enabled": true },
    { "name": "batch", "enabled": true },
    { "name": "dms", "enabled": true },
    { "name": "dms-serverless", "enabled": true }
  ]
}
```