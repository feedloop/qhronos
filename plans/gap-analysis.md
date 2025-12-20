# Qhronos Gap Analysis

## Overview

This document provides a comprehensive gap analysis between the **current implementation** of Qhronos and the **target design** as specified in the design documents. It identifies what exists, what's missing, and what needs to be modified.

---

## 1. Summary

### Current State (v1)
- Basic event scheduling with occurrences
- Webhook, WebSocket, and API Call actions
- Redis-based scheduling with PostgreSQL persistence
- Event archival system
- HMAC signing for webhooks
- JWT/Master token authentication

### Target State (v2)
- Job-based system (renamed from occurrences)
- Schedules in Redis (temporary), Jobs in PostgreSQL (permanent)
- Workflow orchestration with multi-step execution
- Script execution system (Goja JavaScript runtime)
- Integration system (LLM, Notification Channels, Database)
- File system support (Object Storage)
- Execution logging as hierarchical jobs
- Event deletion (no archival)

---

## 2. Feature Gap Matrix

| Feature | Current Status | Target Status | Gap Level |
|---------|---------------|---------------|-----------|
| **Project System (Multi-Tenancy)** |
| Projects Table | ❌ Not Implemented | ✅ New | **New** |
| Project Tokens | ❌ Not Implemented | ✅ JWT-based | **New** |
| Token Generation | ❌ Not Implemented | ✅ New | **New** |
| Resource Isolation | ❌ Not Implemented | ✅ project_id scoping | **New** |
| Project Settings | ❌ Not Implemented | ✅ JSONB config | **New** |
| **Core System** |
| Event CRUD | ✅ Implemented | ✅ Keep (add project_id) | **Modify** |
| Occurrence/Job System | ⚠️ Occurrences | Jobs | **Rename** |
| Logs Table | ❌ Not Implemented | ✅ Separate logs table | **New** |
| Async Job Log Writer | ❌ Not Implemented | ✅ Buffered channel | **New** |
| Logs API | ❌ Not Implemented | ✅ GET /jobs/{id}/logs | **New** |
| Logs Cleanup | ❌ Not Implemented | ✅ Level-based retention | **New** |
| Archival System | ✅ Implemented | ❌ Remove | **Delete** |
| Event Cleanup | ⚠️ Archival-based | Delete on completion | **Modify** |
| **Scheduling** |
| Redis Schedules | ✅ Implemented | ✅ Keep (enhance) | Minor |
| Expander | ✅ Implemented | ⚠️ Add recurrence expiration check | **Modify** |
| Dispatcher | ✅ Implemented | ⚠️ Add event deletion, job creation | **Modify** |
| Cleanup | ✅ Implemented | ⚠️ Change from archival to deletion | **Modify** |
| **Actions** |
| Webhook | ✅ Implemented | ✅ Keep | None |
| WebSocket | ✅ Implemented | ✅ Keep | None |
| API Call | ✅ Implemented | ✅ Keep | None |
| Script | ❌ Not Implemented | ✅ New | **New** |
| Integration | ❌ Not Implemented | ✅ New | **New** |
| Workflow | ❌ Not Implemented | ✅ New | **New** |
| **Workflow System** |
| Workflow CRUD | ❌ Not Implemented | ✅ New | **New** |
| Workflow Engine | ❌ Not Implemented | ✅ New | **New** |
| Step Executor | ❌ Not Implemented | ✅ New | **New** |
| Condition Evaluator | ❌ Not Implemented | ✅ New | **New** |
| Variable System | ❌ Not Implemented | ✅ New | **New** |
| Template Resolution | ❌ Not Implemented | ✅ New | **New** |
| Loop Executor | ❌ Not Implemented | ✅ New | **New** |
| **Script System** |
| Script Repository | ❌ Not Implemented | ✅ New | **New** |
| Goja Runtime | ❌ Not Implemented | ✅ New | **New** |
| Module System | ❌ Not Implemented | ✅ New | **New** |
| Fetch API | ❌ Not Implemented | ✅ New | **New** |
| Console API | ❌ Not Implemented | ✅ New | **New** |
| **Integrations** |
| LLM Integrations | ❌ Not Implemented | ✅ New | **New** |
| Notification Channels | ❌ Not Implemented | ✅ New | **New** |
| Database Integrations | ❌ Not Implemented | ✅ New | **New** |
| Spreadsheet Integrations | ❌ Not Implemented | ✅ New (Google Sheets) | **New** |
| **File System** |
| Object Storage | ❌ Not Implemented | ✅ New | **New** |
| Global Files | ❌ Not Implemented | ✅ New | **New** |
| Workflow Files | ❌ Not Implemented | ✅ New | **New** |
| **Observability** |
| Prometheus Metrics | ❌ Not Implemented | ✅ New | **New** |
| Health/Ready Endpoints | ⚠️ Partial (health only) | ✅ Health + Ready | **Enhance** |
| Metrics Endpoint | ❌ Not Implemented | ✅ New | **New** |
| **Audit Trail** |
| Audit Log Table | ❌ Not Implemented | ✅ New | **New** |
| JWT Claims Logging | ❌ Not Implemented | ✅ user_id, token_id, role | **New** |
| Async Audit Writer | ❌ Not Implemented | ✅ Buffered channel | **New** |
| Audit Log API | ❌ Not Implemented | ✅ Query, export | **New** |
| Audit Retention | ❌ Not Implemented | ✅ Category-based | **New** |
| Audit Sampling | ❌ Not Implemented | ✅ High-volume ops | **New** |
| **Cleanup & Retention** |
| Configurable Retention Policies | ❌ Not Implemented | ✅ New | **New** |
| Cleanup Scheduler | ⚠️ Archival-based | ✅ Deletion-based | **Modify** |
| Admin API Endpoints | ❌ Not Implemented | ✅ New | **New** |
| File Cleanup | ❌ Not Implemented | ✅ New | **New** |
| Audit Log Cleanup | ❌ Not Implemented | ✅ New | **New** |
| Optional Archival | ❌ Not Implemented | ✅ New (optional) | **New** |
| **Scalability & Resilience** |
| Distributed Locking | ❌ Not Implemented | ✅ New | **New** |
| Circuit Breakers | ❌ Not Implemented | ✅ New | **New** |
| Retry Strategies | ⚠️ Basic | ✅ Configurable with backoff | **Enhance** |
| Multi-Instance Support | ⚠️ Partial | ✅ Full horizontal scaling | **Enhance** |
| PostgreSQL HA | ❌ Not Implemented | ✅ Read replicas, failover | **New** |
| Redis HA | ❌ Not Implemented | ✅ Sentinel support | **New** |
| Idempotency Keys | ❌ Not Implemented | ✅ New | **New** |
| Graceful Shutdown | ⚠️ Basic | ✅ Connection draining | **Enhance** |
| Stalled Job Recovery | ❌ Not Implemented | ✅ New | **New** |

---

## 3. Detailed Gap Analysis

### 3.1 Database Schema

#### Current Schema

```
Tables:
├── events (id, name, description, start_time, webhook, action, metadata, schedule, tags, status, hmac_secret, created_at, updated_at)
├── occurrences (id, occurrence_id, event_id, scheduled_at, status, attempt_count, timestamp, status_code, response_body, error_message, started_at, completed_at)
├── archived_events (...)
├── archived_occurrences (...)
└── performance_metrics (...)
```

#### Target Schema

```
Tables:
├── events (KEEP, minor updates)
├── jobs (RENAMED from occurrences, ENHANCED with hierarchical structure, JSONB data field)
├── workflows (NEW)
├── scripts (NEW)
├── integrations (NEW)
├── performance_metrics (KEEP - Prometheus only)
└── archived_* tables (REMOVE)
```

#### Schema Changes Required

1. **Rename `occurrences` → `jobs`**
   - Rename table
   - Rename `occurrence_id` → keep as job identifier or use `id`
   - Add `type` column (job, workflow, step, api_call, script, webhook, websocket, integration)
   - Add `parent_job_id` for hierarchical structure
   - Add `data` JSONB for type-specific fields
   - Add `schedule_id` reference (nullable)

2. **Drop Archival Tables**
   - Drop `archived_events`
   - Drop `archived_occurrences`
   - Drop `archive_old_data()` function

3. **Create New Tables**
   - `workflows` - Workflow definitions
   - `scripts` - Script repository
   - `integrations` - External service connectors

---

### 3.2 Models

#### Current Models (`internal/models/`)

| File | Status | Changes Required |
|------|--------|-----------------|
| `event.go` | Keep | Minor updates (action field already exists) |
| `occurrence.go` | Rename | Rename to `job.go`, add type, parent_job_id, data fields |
| `action.go` | Keep | Add `ActionTypeScript`, `ActionTypeIntegration`, `ActionTypeWorkflow` |
| `token.go` | Keep | No changes |
| `errors.go` | Keep | May need new error types |

#### New Models Required

| File | Description |
|------|-------------|
| `job.go` | Job model with hierarchical structure (replaces occurrence.go) |
| `workflow.go` | Workflow definition model |
| `workflow_instance.go` | → Merged into jobs (job with type='workflow') |
| `script.go` | Script model with versioning |
| `integration.go` | Integration model (LLM, notification, database) |
| `schedule.go` | Already exists, may need updates |

---

### 3.3 Repositories

#### Current Repositories (`internal/repository/`)

| File | Status | Changes Required |
|------|--------|-----------------|
| `event_repository.go` | Keep | Remove archival methods, add delete logic |
| `occurrence_repository.go` | Rename | Rename to `job_repository.go`, update methods |

#### New Repositories Required

| File | Description |
|------|-------------|
| `job_repository.go` | CRUD for jobs with hierarchical queries |
| `workflow_repository.go` | CRUD for workflows |
| `script_repository.go` | CRUD for scripts with versioning |
| `integration_repository.go` | CRUD for integrations |

---

### 3.4 Handlers

#### Current Handlers (`internal/handlers/`)

| File | Status | Changes Required |
|------|--------|-----------------|
| `event_handler.go` | Keep | Minor updates |
| `occurrence_handler.go` | Rename | Rename to `job_handler.go`, update endpoints |
| `status.go` | Keep | No changes |
| `token_handler.go` | Keep | No changes |
| `websocket_handler.go` | Keep | No changes |

#### New Handlers Required

| File | Description |
|------|-------------|
| `job_handler.go` | Job endpoints (renamed from occurrence) |
| `workflow_handler.go` | Workflow CRUD and execution |
| `script_handler.go` | Script CRUD and execution |
| `integration_handler.go` | Integration CRUD |

---

### 3.5 Scheduler Components

#### Current Scheduler (`internal/scheduler/`)

| File | Status | Changes Required |
|------|--------|-----------------|
| `scheduler.go` | Keep | No changes |
| `expander.go` | Modify | Add recurrence expiration check, delete expired events |
| `dispatcher.go` | Modify | Create jobs instead of updating occurrences, delete events |
| `archiver.go` | Remove | Delete entirely |
| `schedule.go` | Keep | No changes |

#### New Scheduler Components

| File | Description |
|------|-------------|
| `workflow_dispatcher.go` | Workflow execution dispatcher |

---

### 3.6 Actions System

#### Current Actions (`internal/actions/`)

| File | Status | Changes Required |
|------|--------|-----------------|
| `manager.go` | Modify | Add script, integration, workflow action types |
| `webhook.go` | Keep | No changes |
| `websocket.go` | Keep | No changes |
| `apicall.go` | Keep | No changes |

#### New Action Executors

| File | Description |
|------|-------------|
| `script.go` | Script action executor |
| `integration.go` | Integration action executor (LLM, notification, database) |
| `workflow.go` | Workflow action executor (triggers sub-workflow) |

---

### 3.7 Workflow System (NEW)

All files in `internal/workflow/` are new:

| File | Description |
|------|-------------|
| `engine.go` | Workflow orchestration engine |
| `state_manager.go` | Workflow state management |
| `executor.go` | Main execution coordinator |
| `step_executor.go` | Individual step executor |
| `condition_evaluator.go` | JavaScript-like condition evaluation |
| `loop_executor.go` | Loop step handling |
| `template.go` | Template variable resolution |
| `variables.go` | Workflow variable management |
| `queue.go` | Redis queue for workflow execution |

---

### 3.8 Script System (NEW)

All files in `internal/script/` are new:

| File | Description |
|------|-------------|
| `runtime.go` | Goja JavaScript runtime wrapper |
| `context.go` | Execution context (input, steps, workflow) |
| `fetch.go` | Fetch API implementation |
| `console.go` | Console API implementation |
| `modules.go` | Module system (require()) |
| `modules/crypto.go` | Crypto module |
| `modules/uuid.go` | UUID module |
| `modules/validator.go` | Validator module |
| `modules/jsonpath.go` | JSONPath module |
| `modules/db.go` | Database module |
| `modules/llm.go` | LLM module |
| `modules/files.go` | Files module |

---

### 3.9 Integration System (NEW)

All files in `internal/integrations/` are new:

| File | Description |
|------|-------------|
| `manager.go` | Integration manager |
| `llm/openai.go` | OpenAI provider |
| `llm/anthropic.go` | Anthropic provider |
| `llm/gemini.go` | Google Gemini provider |
| `llm/openrouter.go` | OpenRouter provider |
| `notification/ses.go` | Amazon SES |
| `notification/twilio.go` | Twilio SMS/Voice |
| `notification/slack.go` | Slack webhook |
| `notification/discord.go` | Discord webhook |
| `notification/telegram.go` | Telegram Bot API |
| `database/mysql.go` | MySQL connector |
| `database/postgres.go` | PostgreSQL connector |
| `spreadsheet/google_sheets.go` | Google Sheets API connector |

---

### 3.10 Storage System (NEW)

All files in `internal/storage/` are new:

| File | Description |
|------|-------------|
| `object_storage.go` | MinIO/S3 client wrapper |
| `file_manager.go` | File path resolution (global, workflow, event, job) |

---

### 3.11 Metrics System (NEW)

All files in `internal/metrics/` are new:

| File | Description |
|------|-------------|
| `metrics.go` | Prometheus metrics registry and definitions |
| `http.go` | HTTP metrics middleware |
| `job.go` | Job execution metrics |
| `workflow.go` | Workflow execution metrics |
| `script.go` | Script execution metrics |
| `integration.go` | Integration metrics (LLM, notification, database) |
| `scheduler.go` | Scheduler component metrics |
| `database.go` | Database connection and query metrics |
| `redis.go` | Redis command metrics |
| `storage.go` | Object storage metrics |

**Prometheus Metrics Categories:**

| Category | Metrics Count | Description |
|----------|---------------|-------------|
| HTTP | 5 | Request count, latency, in-flight, size |
| Events | 3 | Total, created, deleted |
| Schedules | 4 | Total, created, executed, expired |
| Jobs | 4 | Total, duration, in-progress, retries |
| Workflows | 5 | Executions, duration, steps, active |
| Scripts | 3 | Executions, duration, memory |
| Integrations | 3 | Requests, duration, errors |
| LLM | 3 | Tokens, cost, latency |
| Actions | 4 | Executions, duration, webhook deliveries |
| Database | 3 | Connections, queries, duration |
| Redis | 3 | Commands, duration, connections |
| Storage | 3 | Operations, bytes, duration |
| Scheduler | 4 | Runs, duration, errors, processed |
| System | 2 | Uptime, build info |

**New Dependencies:**
- `github.com/prometheus/client_golang` - Prometheus client library

---

### 3.12 Cleanup & Retention System (ENHANCE)

Existing archival-based cleanup needs to be replaced with a comprehensive retention management system.

**Current State:**
- `internal/scheduler/archiver.go` - Archives old data (TO BE REMOVED)

**Target State - Files to Create:**

| File | Description |
|------|-------------|
| `internal/retention/config.go` | Retention policy configuration |
| `internal/retention/policy.go` | Retention policy definitions |
| `internal/retention/manager.go` | Retention policy manager |
| `internal/cleanup/scheduler.go` | Cleanup job scheduler |
| `internal/cleanup/event_cleanup.go` | Event cleanup logic |
| `internal/cleanup/schedule_cleanup.go` | Schedule cleanup (Redis) |
| `internal/cleanup/job_cleanup.go` | Job cleanup logic |
| `internal/cleanup/log_cleanup.go` | Log cleanup logic |
| `internal/cleanup/file_cleanup.go` | File cleanup (object storage) |
| `internal/handlers/admin_handler.go` | Admin API endpoints |
| `internal/archival/exporter.go` | Optional data archival (S3/GCS) |

**Cleanup Metrics:**

| Metric | Type | Description |
|--------|------|-------------|
| `qhronos_cleanup_runs_total` | Counter | Cleanup runs by component |
| `qhronos_cleanup_duration_seconds` | Histogram | Cleanup duration |
| `qhronos_cleanup_records_deleted_total` | Counter | Records deleted by type |
| `qhronos_cleanup_bytes_freed_total` | Counter | Storage freed |
| `qhronos_cleanup_errors_total` | Counter | Cleanup errors |
| `qhronos_retention_oldest_job_age_seconds` | Gauge | Age of oldest job |
| `qhronos_storage_usage_bytes` | Gauge | Storage usage by scope |

**Admin API Endpoints:**

| Endpoint | Description |
|----------|-------------|
| `GET /admin/retention` | Get retention policies |
| `PUT /admin/retention` | Update retention policies |
| `POST /admin/cleanup/run` | Trigger manual cleanup |
| `GET /admin/cleanup/status` | Cleanup status |
| `GET /admin/cleanup/history` | Cleanup history |
| `DELETE /admin/jobs/expired` | Force delete expired jobs |
| `DELETE /admin/files/orphaned` | Force delete orphaned files |
| `GET /admin/storage/usage` | Storage usage stats |

---

### 3.13 API Routes

#### Current Routes (`internal/api/routes.go`)

```
Current Endpoints:
├── POST   /events
├── GET    /events/{id}
├── PUT    /events/{id}
├── DELETE /events/{id}
├── GET    /events
├── GET    /occurrences
├── GET    /occurrences/{id}
├── GET    /events/{id}/occurrences
├── POST   /tokens
├── GET    /status
├── GET    /health
└── WS     /ws
```

#### Target Routes

```
Target Endpoints:
├── Events (KEEP)
│   ├── POST   /events
│   ├── GET    /events/{id}
│   ├── PUT    /events/{id}
│   ├── DELETE /events/{id}
│   ├── GET    /events
│   └── GET    /events/{id}/jobs
│
├── Jobs (RENAMED from occurrences)
│   ├── GET    /jobs/{id}
│   ├── GET    /jobs
│   └── GET    /jobs/{id}/children
│
├── Workflows (NEW)
│   ├── POST   /workflows
│   ├── GET    /workflows/{id}
│   ├── PUT    /workflows/{id}
│   ├── DELETE /workflows/{id}
│   ├── GET    /workflows
│   ├── POST   /workflows/{id}/execute
│   └── GET    /workflows/{id}/jobs
│
├── Scripts (NEW)
│   ├── POST   /scripts
│   ├── GET    /scripts/{id}
│   ├── PUT    /scripts/{id}
│   ├── DELETE /scripts/{id}
│   ├── GET    /scripts
│   ├── POST   /scripts/{id}/execute
│   └── GET    /scripts/{id}/jobs
│
├── Integrations (NEW)
│   ├── POST   /integrations
│   ├── GET    /integrations/{id}
│   ├── PUT    /integrations/{id}
│   ├── DELETE /integrations/{id}
│   ├── GET    /integrations
│   └── GET    /integrations/{id}/jobs
│
├── Schedules (NEW - for monitoring)
│   └── GET    /schedules
│
├── Tokens (KEEP)
│   └── POST   /tokens
│
└── System (KEEP + NEW)
    ├── GET    /status
    ├── GET    /health
    ├── GET    /ready (NEW)
    ├── GET    /metrics (NEW - Prometheus)
    └── WS     /ws
```

---

## 4. Dependencies Gap

### Current Dependencies (`go.mod`)

| Dependency | Status |
|------------|--------|
| `gin-gonic/gin` | Keep |
| `jmoiron/sqlx` | Keep |
| `go-redis/redis` | Keep |
| `google/uuid` | Keep |
| `lib/pq` | Keep |
| `golang-jwt/jwt` | Keep |
| `go.uber.org/zap` | Keep |

### New Dependencies Required

| Dependency | Purpose |
|------------|---------|
| `github.com/dop251/goja` | Goja JavaScript runtime |
| `github.com/minio/minio-go/v7` | MinIO/S3 client |
| `github.com/sashabaranov/go-openai` | OpenAI API client |
| `github.com/aws/aws-sdk-go-v2/service/ses` | Amazon SES |
| `github.com/twilio/twilio-go` | Twilio client |
| `github.com/go-sql-driver/mysql` | MySQL driver (for script db module) |
| `github.com/prometheus/client_golang` | Prometheus metrics client |

---

## 5. Configuration Gap

### Current Configuration

```yaml
# config.example.yml
server:
  port: 8080
  mode: development

database:
  host: localhost
  port: 5432
  # ...

redis:
  host: localhost
  port: 6379
  # ...

auth:
  master_token: "..."
  jwt_secret: "..."
```

### Additional Configuration Required

```yaml
# New configuration sections
object_storage:
  endpoint: "localhost:9000"
  access_key: "..."
  secret_key: "..."
  bucket: "qhronos"
  use_ssl: false

workflow:
  default_timeout_ms: 300000
  max_step_retries: 3
  queue_concurrency: 10

script:
  timeout_ms: 30000
  memory_limit_mb: 128

# Integration credentials (via integrations API, not config)
```

---

## 6. Migration Complexity Assessment

### Low Complexity (Straightforward)
- Rename occurrences → jobs (table, model, repository, handler)
- Drop archival tables
- Update API routes

### Medium Complexity (Moderate Effort)
- Implement script repository and CRUD
- Implement workflow repository and CRUD
- Implement integration repository and CRUD
- Update dispatcher to create jobs and delete events
- Update expander for recurrence expiration

### High Complexity (Significant Effort)
- Implement Goja JavaScript runtime with sandboxing
- Implement workflow engine and step executor
- Implement condition evaluator (JavaScript-like expressions)
- Implement loop executor (while, foreach)
- Implement variable system and template resolution
- Implement LLM integrations (multiple providers)
- Implement notification channel integrations
- Implement database integrations
- Implement object storage integration

---

## 7. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Data loss during migration | High | Low | Backup before migration, staged rollout |
| Breaking API changes | Medium | Medium | API versioning, deprecation notices |
| Performance degradation | Medium | Medium | Load testing, optimization |
| Security vulnerabilities in script runtime | High | Medium | Sandboxing, resource limits |
| Integration failures | Medium | Medium | Retry logic, circuit breakers |

---

## 8. Implementation Priority

### Phase 1: Core System Refactoring (Weeks 1-3)
1. Database schema changes (occurrences → jobs with hierarchical structure)
2. Remove archival tables and code
3. Update dispatcher for job creation and event deletion
4. Update expander for recurrence expiration

### Phase 2: API Updates & Testing (Weeks 4-5)
1. Update API endpoints (`/occurrences` → `/jobs`)
2. Add hierarchical job queries
3. Comprehensive testing
4. Migration script validation

### Phase 3: Workflow System (Weeks 6-8)
1. Workflow repository with CRUD
2. Workflow engine core
3. Step executor and condition evaluator
4. Loop executor and sub-workflows
5. Variable system and template resolution
6. Workflow API endpoints

### Phase 4: Script System (Weeks 9-11)
1. Script repository with versioning
2. Goja runtime integration
3. Module system (`require()`)
4. Built-in modules (crypto, uuid, validator, jsonpath)
5. Fetch and console APIs
6. Script action executor
7. Script API endpoints

### Phase 5: Integration System (Weeks 12-13)
1. Integration repository with credential encryption
2. LLM integrations (OpenAI, Anthropic, Gemini, OpenRouter)
3. Notification integrations (SES, Twilio, Slack, Discord, Telegram)
4. Database integrations (MySQL, PostgreSQL)
5. Integration action executor
6. Script modules (`require('llm')`, `require('db')`)

### Phase 6: File System (Week 14)
1. Object storage integration (MinIO/S3)
2. File operations in scripts (`require('files')`)
3. File scope management (global, workflow, event, job)

### Phase 7: Observability & Metrics (Week 15)
1. Prometheus metrics infrastructure
2. HTTP, business, and infrastructure metrics
3. `/metrics` and `/ready` endpoints
4. Grafana dashboard templates

### Phase 8: Cleanup & Retention (Week 16)
1. Configurable retention policies
2. Cleanup scheduler components
3. Event, schedule, job, file cleanup
4. Admin API endpoints
5. Cleanup metrics
6. Optional archival support

### Phase 9: Scalability & Resilience (Weeks 17-18)
1. Distributed locking and work distribution
2. Circuit breakers and retry strategies
3. PostgreSQL read replica and Redis Sentinel support
4. Idempotency and distributed tracing
5. Kubernetes manifests and Helm chart
6. Operations documentation

---

## 9. Effort Estimation

| Phase | Component | Duration | Dependencies |
|-------|-----------|----------|--------------|
| 1 | Core System Refactoring | 3 weeks | None |
| 2 | API Updates & Testing | 2 weeks | Phase 1 |
| 3 | Workflow System | 3 weeks | Phase 2 |
| 4 | Script System | 3 weeks | Phase 3 (partial) |
| 5 | Integration System | 2 weeks | Phase 4 |
| 6 | File System | 1 week | Phase 5 |
| 7 | Observability & Metrics | 1 week | Phase 2 |
| 8 | Cleanup & Retention | 1 week | Phase 6 |
| 9 | Scalability & Resilience | 2 weeks | Phase 2 |
| **Total** | | **18 weeks** | |

**Note:** Phases 7, 8, and 9 can run in parallel with Phases 3-6, reducing total time to ~16 weeks.

---

## 10. Success Metrics

### Phase 1-2: Core System
- [ ] `occurrences` table renamed to `jobs` with hierarchical structure
- [ ] Archival tables and code removed
- [ ] Events deleted on completion/expiration
- [ ] `/jobs` API endpoints working
- [ ] All tests passing
- [ ] Migration script validated

### Phase 3: Workflow System
- [ ] Workflow CRUD working
- [ ] All step types working (action, condition, delay, loop, sub_workflow, set_variable)
- [ ] Variable system and template resolution working
- [ ] Workflow API endpoints working

### Phase 4: Script System
- [ ] Script CRUD with versioning working
- [ ] Goja runtime with sandboxing working
- [ ] All modules working (crypto, uuid, validator, jsonpath)
- [ ] Fetch and console APIs working

### Phase 5: Integration System
- [ ] Integration CRUD working
- [ ] LLM integrations working
- [ ] Notification integrations working
- [ ] Database integrations working
- [ ] Script modules (`require('llm')`, `require('db')`) working

### Phase 6: File System
- [ ] Object storage integration working
- [ ] File operations in scripts working
- [ ] All file scopes working (global, workflow, event, job)

### Phase 7: Observability
- [ ] Prometheus metrics endpoint working
- [ ] All metric categories implemented
- [ ] Grafana dashboards created

### Phase 8: Cleanup & Retention
- [ ] Configurable retention policies working
- [ ] Cleanup scheduler working
- [ ] Admin API endpoints working

### Phase 9: Scalability & Resilience
- [ ] Distributed locking working (no duplicate schedules)
- [ ] Atomic job claiming working (no duplicate dispatches)
- [ ] Circuit breakers working for all external dependencies
- [ ] Retry strategies with exponential backoff working
- [ ] PostgreSQL read replica support working
- [ ] Redis Sentinel support working
- [ ] Graceful shutdown with connection draining working
- [ ] Stalled job recovery working
- [ ] Idempotency key support working
- [ ] Distributed tracing (OpenTelemetry) working
- [ ] Kubernetes deployment manifests created
- [ ] Horizontal Pod Autoscaler configured
- [ ] Operations documentation complete

### Overall
- [ ] All tests passing (>80% coverage)
- [ ] API documentation updated
- [ ] Client SDKs updated
- [ ] Load testing completed (target: 10K events/minute)
- [ ] Failover testing completed

---

## 11. Conclusion

The gap between the current implementation and the target design is significant but manageable. The core refactoring (occurrences → jobs, removing archival) is straightforward, while the new systems (workflows, scripts, integrations) require substantial development effort.

**Key Recommendations:**
1. Start with core refactoring to establish the new data model
2. Build workflow engine incrementally (start with simple sequential flows)
3. Implement script system with security as a priority
4. Add integrations one at a time (start with OpenAI)
5. Extensive testing at each phase
6. Implement scalability features early to validate architecture
7. Load test before production deployment

The estimated timeline of 18 weeks (16 with parallel execution) is achievable with focused development.

