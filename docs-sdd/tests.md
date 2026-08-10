# Test Specification — AWS Lambda Shutdown of AWS Services

## Test Strategy

- **Unit tests:** pytest with `unittest.mock` / `moto`, covering core logic in isolation.
- **Integration tests:** end-to-end flow with mocked AWS services (moto).
- **Acceptance tests:** mapped to the acceptance criteria in `docs-sdd/feature.md`.
- **Coverage target:** high coverage of config parsing, schedule matching, handlers, notifier, and scheduler generation.

## Unit Tests

### Config Parsing & Validation (US-001, US-002, US-003)

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| UT-001 | Load a valid `config.json`. | Returns parsed configuration. |
| UT-002 | Load a missing file. | Raises a clear error. |
| UT-003 | Validate invalid JSON (bad syntax). | Validation error raised. |
| UT-004 | Validate missing `general` section. | Config considered invalid. |
| UT-005 | Validate invalid `daysOfWeek` value. | Config rejected. |
| UT-006 | Validate invalid time format in `times`. | Config rejected. |
| UT-007 | Service without `schedule` inherits general config. | Inherited schedule returned. |
| UT-008 | Service-specific `schedule` overrides general. | Specific schedule returned. |

### Schedule Matching (US-002, US-003)

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| UT-009 | Current time/day matches a specific schedule. | Service processed. |
| UT-010 | Current time/day does not match. | Service skipped. |
| UT-011 | Multiple times in `times` list. | Matches any configured time. |
| UT-012 | Inherited general schedule matching. | Service processed per general config. |

### Forced Shutdown of All Items (US-004)

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| UT-013 | EC2 handler lists and stops all active instances. | All active instances stopped. |
| UT-014 | EC2 handler ignores already-stopped instances. | No error; stopped instances skipped. |
| UT-015 | RDS handler stops all active DB instances. | All active instances stopped. |
| UT-016 | ECS handler scales all services to zero. | All services scaled to 0. |
| UT-017 | Glue handler (batch) stops running job runs. | All running job runs stopped. |
| UT-018 | Glue handler (streaming) stops running job runs. | All running job runs stopped. |
| UT-019 | Aurora handler stops all active DB clusters. | All active clusters stopped. |
| UT-020 | Batch handler terminates all running jobs. | All running jobs terminated. |
| UT-021 | DMS handler stops replication tasks and instances. | Tasks/instances stopped. |
| UT-022 | DMS Serverless handler stops replication configs. | All replication configs stopped. |
| UT-023 | Unknown service name. | Factory raises clear error. |

### SNS Notification on Failure (US-005)

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| UT-024 | Item fails to shut down. | SNS publish called with failure details. |
| UT-025 | Error occurs during execution. | SNS publish called. |
| UT-026 | No failures. | No SNS publish. |
| UT-027 | Missing/invalid JSON. | SNS publish to `FALLBACK_NOTIFICATION_EMAIL`. |

### EventBridge Scheduler Generation (US-006, US-007)

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| UT-028 | Generate one scheduler per unique time. | Correct schedulers created. |
| UT-029 | Idempotency: run generation twice. | No duplicate schedulers. |
| UT-030 | Removed configuration. | Scheduler removed. |
| UT-031 | Generate schedulers with services set to `enabled: false`. | Schedulers still created from all services' times and always **ENABLED**. |
| UT-032 | Re-run generation after toggling `enabled`. | Same scheduler set; no `update_schedule` calls; state unchanged. |

## Integration Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| IT-001 | Full handler flow with valid config (moto). | Services shut down; no email. |
| IT-002 | Full handler flow with one failing item. | Email sent with failure details. |
| IT-003 | Full handler flow with invalid config. | Execution aborted; fallback email sent. |
| IT-004 | Scheduler generation end-to-end. | Schedulers created and idempotent. |

## Infrastructure Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| INF-001 | `terraform validate` on the `infra/` module. | Module is valid. |
| INF-002 | `terraform fmt --check` on the `infra/` module. | All files are formatted. |
| INF-003 | `main.tf` contains only the main resources. | No auxiliary resources (IAM, SNS, S3) in `main.tf`. |

## Acceptance Tests

Each acceptance criterion in `docs-sdd/feature.md` (US-001 to US-007) must have a corresponding passing test:

| User Story | Acceptance Test |
|------------|-----------------|
| US-001 | AT-001: only listed services shut down; missing/invalid JSON aborts and notifies fallback email. |
| US-002 | AT-002: services without schedule use general config. |
| US-003 | AT-003: service-specific schedule overrides general. |
| US-004 | AT-004: all items forcibly shut down; already-stopped ignored. |
| US-005 | AT-005: email sent on failure with details; no email when no failures. |
| US-006 | AT-006: schedulers generated per unique time, idempotent, cleaned up. |
| US-007 | AT-007: service with `enabled: false` is skipped by the Lambda while its scheduler stays ENABLED and the scheduler set is unchanged. |