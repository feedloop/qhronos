# Qhronos v2 Implementation Plan

## Overview

This document outlines the implementation plan for Qhronos v2, transitioning from the current occurrence-based system to a comprehensive job-based workflow orchestration platform.

### Key Changes from v1 to v2

1. **Rename "occurrences" to "jobs"** - Unified job table for all execution records
2. **Remove event archival** - Events deleted when done, jobs retained as audit trail
3. **Unified jobs table** - Hierarchical job structure (job → workflow → step → action)
4. **Schedules in Redis** - Temporary scheduled executions
5. **Workflow system** - Multi-step orchestration with conditions, loops, sub-workflows
6. **Script system** - JavaScript execution with Goja runtime
7. **Integration system** - LLM, notification channels, database connectors
8. **File system** - Object storage (MinIO/S3) integration
9. **Observability** - Prometheus metrics, Grafana dashboards
10. **Retention management** - Configurable cleanup policies

---

## Phase 1: Core System Refactoring

**Duration:** 3 weeks  
**Dependencies:** None

### 1.1 Project System (Multi-Tenancy)

**Week 1: Project & Token Tables**

**Tasks:**
- [ ] Create `projects` table migration
- [ ] Create `project_tokens` table migration
- [ ] Create `Project` model with settings JSONB
- [ ] Create `ProjectToken` model
- [ ] Implement project repository (CRUD)
- [ ] Implement project token repository (create, list, revoke)
- [ ] Implement JWT token generation for projects
- [ ] Implement JWT token validation middleware
- [ ] Add project_id to all major tables (events, workflows, scripts, integrations, jobs)
- [ ] Implement project-scoped query filtering

**Schema:**
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    settings JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE project_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    scopes TEXT[] NOT NULL DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Files to Create:**
- `migrations/002_create_projects_table.sql`
- `internal/models/project.go`
- `internal/models/project_token.go`
- `internal/repository/project_repository.go`
- `internal/repository/project_token_repository.go`
- `internal/auth/jwt.go`
- `internal/middleware/auth.go`
- `internal/middleware/project.go`
- `internal/handlers/project_handler.go`

### 1.2 Database Schema Changes

**Week 1-2: Jobs Table Migration**

**Tasks:**
- [ ] Create migration to rename `occurrences` table to `jobs`
- [ ] Add `type` column (job, workflow, step, api_call, script, webhook, websocket, integration)
- [ ] Add `parent_job_id` for hierarchical structure
- [ ] Add `data` JSONB for type-specific fields
- [ ] Add `schedule_id` reference (nullable)
- [ ] Add `project_id` foreign key to all tables
- [ ] Update all indexes and constraints
- [ ] Drop archival tables (`archived_events`, `archived_occurrences`)
- [ ] Remove `archive_old_data()` function

**Schema:**
```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id), -- NULL for system jobs
    schedule_id UUID,
    type VARCHAR(50) NOT NULL CHECK (type IN ('job', 'workflow', 'step', 'api_call', 'script', 'webhook', 'websocket', 'integration')),
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    is_system BOOLEAN NOT NULL DEFAULT FALSE, -- True for internal/system jobs
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    error_message TEXT,
    parent_job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Files to Modify:**
- `migrations/003_rename_occurrences_to_jobs.sql`
- `internal/models/occurrence.go` → `internal/models/job.go`
- `internal/repository/occurrence_repository.go` → `internal/repository/job_repository.go`

### 1.3 Code Refactoring

**Week 2: Model and Repository Updates**

**Tasks:**
- [ ] Rename `Occurrence` model to `Job`
- [ ] Add `JobType`, `ParentJobID`, `ProjectID`, `IsSystem`, `Data` fields
- [ ] Update repository interface and implementation
- [ ] Add project-scoped filtering to all repository methods
- [ ] Add system job filtering (exclude `is_system=true` unless admin token)
- [ ] Update handler endpoints (`/occurrences` → `/jobs`)
- [ ] Add admin token check middleware for system job access
- [ ] Remove archival scheduler component
- [ ] Remove archival methods from repositories

**Files to Modify:**
- `internal/models/job.go` (new)
- `internal/repository/job_repository.go` (new)
- `internal/handlers/occurrence_handler.go` → `internal/handlers/job_handler.go`
- `internal/scheduler/archiver.go` (delete)

### 1.4 Scheduler Updates

**Week 3: Dispatcher and Expander**

**Tasks:**
- [ ] Update Expander to check recurrence expiration
- [ ] Update Expander to delete expired events
- [ ] Update Dispatcher to create jobs instead of updating occurrences
- [ ] Update Dispatcher to delete events after job completion
- [ ] Update Cleanup to use deletion instead of archival

**Files to Modify:**
- `internal/scheduler/expander.go`
- `internal/scheduler/dispatcher.go`
- `internal/scheduler/cleanup.go`

---

## Phase 2: API Updates & Testing

**Duration:** 2 weeks  
**Dependencies:** Phase 1

### 2.1 API Endpoint Updates

**Week 4: Endpoint Refactoring**

**Tasks:**
- [ ] Update `/occurrences` endpoints to `/jobs`
- [ ] Add `/jobs/{id}/children` endpoint
- [ ] Add `/jobs/{id}/logs` endpoint
- [ ] Add hierarchical job queries
- [ ] Update response models
- [ ] Update API documentation

**Endpoint Changes:**
- `GET /occurrences` → `GET /jobs`
- `GET /occurrences/{id}` → `GET /jobs/{id}`
- `GET /events/{id}/occurrences` → `GET /events/{id}/jobs`
- `GET /jobs/{id}/children` (new)
- `GET /jobs/{id}/logs` (new)

**Files to Modify:**
- `internal/api/routes.go`
- `internal/handlers/job_handler.go`
- `docs/api.md`

### 2.2 Logs System

**Week 4: Logs Implementation**

**Tasks:**
- [ ] Create `logs` table migration
- [ ] Create `Log` model
- [ ] Implement log repository with batch insert
- [ ] Implement async log writer with buffered channel
- [ ] Add log API endpoint (`GET /jobs/{id}/logs`)
- [ ] Implement log level filtering and pagination
- [ ] Add data size limits and truncation
- [ ] Implement log metrics

**Schema:**
```sql
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    level VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL,
    message TEXT,
    data JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Files to Create:**
- `migrations/004_create_logs_table.sql`
- `internal/models/log.go`
- `internal/repository/log_repository.go`
- `internal/logs/writer.go`
- `internal/logs/buffer.go`
- `internal/handlers/log_handler.go`
- `internal/metrics/logs.go`

### 2.3 Testing & Migration

**Week 5: Testing and Validation**

**Tasks:**
- [ ] Update existing occurrence tests to job tests
- [ ] Add hierarchical job query tests
- [ ] Test event deletion logic
- [ ] Test job creation from dispatcher
- [ ] Create data migration script
- [ ] Test migration in staging environment
- [ ] Update README and documentation

**Files to Modify/Create:**
- `internal/repository/job_repository_test.go`
- `internal/handlers/job_handler_test.go`
- `internal/scheduler/dispatcher_test.go`
- `scripts/migrate_v1_to_v2.sql`

---

## Phase 3: Workflow System

**Duration:** 3 weeks  
**Dependencies:** Phase 2

### 3.1 Workflow Repository

**Week 6: Database and Repository**

**Tasks:**
- [ ] Create workflows table migration
- [ ] Create `Workflow` model
- [ ] Create workflow repository with CRUD
- [ ] Add versioning support
- [ ] Add tag-based queries

**Schema:**
```sql
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    definition JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    tags TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

**Files to Create:**
- `migrations/004_create_workflows_table.sql`
- `internal/models/workflow.go`
- `internal/repository/workflow_repository.go`

### 3.2 Workflow Engine Core

**Week 7: Engine Implementation**

**Tasks:**
- [ ] Create workflow engine interface
- [ ] Implement step executor
- [ ] Implement condition evaluator (JavaScript-like expressions)
- [ ] Implement template resolution (`{{variable.path}}`)
- [ ] Implement variable system
- [ ] Implement delay step
- [ ] Implement set_variable step

**Files to Create:**
- `internal/workflow/engine.go`
- `internal/workflow/executor.go`
- `internal/workflow/step_executor.go`
- `internal/workflow/condition_evaluator.go`
- `internal/workflow/template.go`
- `internal/workflow/variables.go`

### 3.3 Workflow Advanced Features

**Week 8: Loops, Sub-workflows, API**

**Tasks:**
- [ ] Implement loop executor (while and foreach)
- [ ] Implement sub-workflow execution
- [ ] Implement workflow timeout handling
- [ ] Implement retry logic per step
- [ ] Create workflow dispatcher (background job)
- [ ] Create workflow API handlers
- [ ] Add workflow routes

**Files to Create:**
- `internal/workflow/loop_executor.go`
- `internal/workflow/state_manager.go`
- `internal/workflow/queue.go`
- `internal/scheduler/workflow_dispatcher.go`
- `internal/handlers/workflow_handler.go`

---

## Phase 4: Script System

**Duration:** 3 weeks  
**Dependencies:** Phase 3 (partial - can start Week 7)

### 4.1 Script Repository

**Week 9: Database and Repository**

**Tasks:**
- [ ] Create scripts table migration
- [ ] Create `Script` model with versioning
- [ ] Create script repository with CRUD
- [ ] Add version management (new version on update)

**Schema:**
```sql
CREATE TABLE scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    code TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    language VARCHAR(50) NOT NULL DEFAULT 'javascript',
    tags TEXT[] NOT NULL DEFAULT '{}',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

**Files to Create:**
- `migrations/005_create_scripts_table.sql`
- `internal/models/script.go`
- `internal/repository/script_repository.go`

### 4.2 Goja Runtime Integration

**Week 10: JavaScript Runtime**

**Tasks:**
- [ ] Add Goja dependency
- [ ] Create script runtime wrapper
- [ ] Implement execution context (input, steps, workflow, console)
- [ ] Implement timeout and resource limits
- [ ] Implement module system (`require()`)
- [ ] Implement built-in modules (crypto, uuid, validator, jsonpath)

**Files to Create:**
- `internal/script/runtime.go`
- `internal/script/context.go`
- `internal/script/modules.go`
- `internal/script/modules/crypto.go`
- `internal/script/modules/uuid.go`
- `internal/script/modules/validator.go`
- `internal/script/modules/jsonpath.go`

### 4.3 Script APIs and Integration

**Week 11: APIs and Workflow Integration**

**Tasks:**
- [ ] Implement `fetch()` API
- [ ] Implement `console` API
- [ ] Create script action executor
- [ ] Integrate script execution with workflow steps
- [ ] Extract variables from script output (`_variables`)
- [ ] Create script API handlers
- [ ] Add script routes
- [ ] Add `POST /scripts/{id}/execute` endpoint

**Files to Create:**
- `internal/script/fetch.go`
- `internal/script/console.go`
- `internal/actions/script.go`
- `internal/handlers/script_handler.go`

---

## Phase 5: Integration System

**Duration:** 2 weeks  
**Dependencies:** Phase 4

### 5.1 Integration Repository

**Week 12: Database and Repository**

**Tasks:**
- [ ] Create integrations table migration
- [ ] Create `Integration` model
- [ ] Create integration repository with CRUD
- [ ] Implement credential encryption
- [ ] Create integration manager

**Schema:**
```sql
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('llm', 'notification', 'database', 'spreadsheet')),
    provider VARCHAR(100) NOT NULL,
    config JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

**Files to Create:**
- `migrations/006_create_integrations_table.sql`
- `internal/models/integration.go`
- `internal/repository/integration_repository.go`
- `internal/integrations/manager.go`

### 5.2 Integration Providers

**Week 13: Provider Implementations**

**Tasks:**
- [ ] Implement LLM integrations (OpenAI, Anthropic, Gemini, OpenRouter)
- [ ] Implement notification integrations (SES, Twilio, Slack, Discord, Telegram)
- [ ] Implement database integrations (MySQL, PostgreSQL)
- [ ] Implement spreadsheet integrations (Google Sheets)
- [ ] Create integration action executor
- [ ] Integrate with script module system (`require('llm')`, `require('db')`, `require('sheets')`)
- [ ] Create integration API handlers

**Files to Create:**
- `internal/integrations/llm/openai.go`
- `internal/integrations/llm/anthropic.go`
- `internal/integrations/llm/gemini.go`
- `internal/integrations/llm/openrouter.go`
- `internal/integrations/notification/ses.go`
- `internal/integrations/notification/twilio.go`
- `internal/integrations/notification/slack.go`
- `internal/integrations/database/mysql.go`
- `internal/integrations/database/postgres.go`
- `internal/integrations/spreadsheet/google_sheets.go`
- `internal/actions/integration.go`
- `internal/handlers/integration_handler.go`
- `internal/script/modules/llm.go`
- `internal/script/modules/db.go`
- `internal/script/modules/sheets.go`

---

## Phase 6: File System

**Duration:** 1 week  
**Dependencies:** Phase 5

### 6.1 Object Storage Integration

**Week 14: Storage Implementation**

**Tasks:**
- [ ] Add MinIO client dependency
- [ ] Create object storage wrapper
- [ ] Implement file path resolution (global, workflow, event, job)
- [ ] Implement file operations (read, write, list, delete)
- [ ] Create files script module (`require('files')`)
- [ ] Implement file cleanup based on scope

**Files to Create:**
- `internal/storage/object_storage.go`
- `internal/storage/file_manager.go`
- `internal/script/modules/files.go`

---

## Phase 7: Observability & Metrics

**Duration:** 1 week  
**Dependencies:** Phase 2 (can run parallel to Phases 3-6)

### 7.1 Prometheus Metrics

**Week 15: Metrics Implementation**

**Tasks:**
- [ ] Add Prometheus client dependency
- [ ] Create metrics registry and definitions
- [ ] Implement HTTP metrics middleware
- [ ] Implement business metrics (events, schedules, jobs)
- [ ] Implement workflow and script metrics
- [ ] Implement integration metrics
- [ ] Implement infrastructure metrics (database, Redis, storage)
- [ ] Create `/metrics` endpoint
- [ ] Create `/ready` endpoint
- [ ] Create Grafana dashboard templates

**Files to Create:**
- `internal/metrics/metrics.go`
- `internal/metrics/http.go`
- `internal/metrics/business.go`
- `internal/metrics/workflow.go`
- `internal/metrics/script.go`
- `internal/metrics/integration.go`
- `internal/metrics/infrastructure.go`
- `internal/handlers/metrics_handler.go`
- `grafana/dashboards/*.json`

---

## Phase 8: Cleanup, Retention & Audit Trail

**Duration:** 2 weeks  
**Dependencies:** Phase 6

### 8.1 Audit Trail System

**Week 16: Audit Implementation**

**Tasks:**
- [ ] Create audit_logs table migration
- [ ] Create `AuditLog` model with all required fields
- [ ] Implement audit log repository with batch insert
- [ ] Implement async audit writer with buffered channel
- [ ] Create audit middleware to capture JWT claims (user_id, token_id, role)
- [ ] Implement action-specific audit logging (events, jobs, workflows, etc.)
- [ ] Add before/after state capture for mutations
- [ ] Implement sensitive field redaction (passwords, api_keys, secrets)
- [ ] Add audit sampling configuration for high-volume operations
- [ ] Create audit log API endpoints (`GET /admin/audit-logs`, export)
- [ ] Implement audit metrics (buffer size, flush duration, dropped logs)

**Schema:**
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    user_id VARCHAR(255),
    token_id VARCHAR(255),
    tenant_id VARCHAR(255),
    role VARCHAR(50),
    actor_type VARCHAR(50) NOT NULL,
    actor_metadata JSONB,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    method VARCHAR(10),
    path VARCHAR(500),
    request_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    before_state JSONB,
    after_state JSONB,
    changes JSONB,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Files to Create:**
- `migrations/007_create_audit_logs_table.sql`
- `internal/models/audit_log.go`
- `internal/repository/audit_log_repository.go`
- `internal/audit/writer.go`
- `internal/audit/buffer.go`
- `internal/audit/middleware.go`
- `internal/audit/redactor.go`
- `internal/handlers/audit_handler.go`
- `internal/metrics/audit.go`

### 8.2 Retention & Cleanup System

**Week 17: Cleanup Implementation**

**Tasks:**
- [ ] Create retention policy configuration
- [ ] Implement retention policy manager
- [ ] Implement cleanup scheduler
- [ ] Implement event cleanup
- [ ] Implement schedule cleanup (Redis)
- [ ] Implement job cleanup with cascading
- [ ] Implement logs cleanup (6h interval, level-based retention)
- [ ] Implement file cleanup
- [ ] Implement audit log cleanup (daily, category-based retention)
- [ ] Create admin API endpoints
- [ ] Implement cleanup metrics
- [ ] Implement optional archival to S3/GCS

**Files to Create:**
- `internal/retention/config.go`
- `internal/retention/policy.go`
- `internal/retention/manager.go`
- `internal/cleanup/scheduler.go`
- `internal/cleanup/event_cleanup.go`
- `internal/cleanup/schedule_cleanup.go`
- `internal/cleanup/job_cleanup.go`
- `internal/cleanup/log_cleanup.go`
- `internal/cleanup/file_cleanup.go`
- `internal/cleanup/audit_log_cleanup.go`
- `internal/handlers/admin_handler.go`
- `internal/archival/exporter.go` (optional)

---

## Phase 9: Scalability & Resilience

**Duration:** 2 weeks  
**Dependencies:** Phase 2 (can run parallel to Phases 3-8)

### 9.1 Distributed Work Distribution

**Week 17: Multi-Instance Support**

**Tasks:**
- [ ] Implement distributed locking for Expander (Redis SETNX)
- [ ] Implement atomic job claiming for Dispatcher (ZPOPMIN)
- [ ] Implement workflow job queue with BRPOPLPUSH
- [ ] Add instance ID tracking for debugging
- [ ] Implement leader election for Cleanup workers
- [ ] Add worker heartbeat mechanism

**Files to Create/Modify:**
- `internal/scheduler/distributed_lock.go`
- `internal/scheduler/worker_pool.go`
- `internal/scheduler/leader_election.go`
- `internal/scheduler/expander.go` (modify)
- `internal/scheduler/dispatcher.go` (modify)
- `internal/workflow/queue.go` (modify)

### 9.2 Circuit Breaker & Resilience

**Week 17: Fault Tolerance (continued)**

**Tasks:**
- [ ] Implement circuit breaker pattern
- [ ] Add circuit breakers for database, Redis, integrations
- [ ] Implement per-URL circuit breaker for webhooks
- [ ] Add retry strategies with exponential backoff
- [ ] Implement graceful shutdown with connection draining
- [ ] Add stalled job detection and recovery

**Files to Create:**
- `internal/resilience/circuit_breaker.go`
- `internal/resilience/retry.go`
- `internal/resilience/health.go`
- `internal/scheduler/recovery.go`

### 9.3 High Availability Support

**Week 18: HA Configuration**

**Tasks:**
- [ ] Add PostgreSQL read replica support
- [ ] Add Redis Sentinel support
- [ ] Add connection pooling configuration
- [ ] Implement health checks for all dependencies
- [ ] Add `/ready` endpoint with dependency checks
- [ ] Implement idempotency key support for API
**Files to Create/Modify:**
- `internal/database/pool.go`
- `internal/database/replica.go`
- `internal/redis/sentinel.go`
- `internal/handlers/health_handler.go` (modify)
- `internal/middleware/idempotency.go`

### 9.4 Deployment Configuration

**Week 18: Production Readiness (continued)**

**Tasks:**
- [ ] Create Kubernetes deployment manifests
- [ ] Create Helm chart
- [ ] Document horizontal scaling configuration
- [ ] Create auto-scaling policies (HPA)
- [ ] Document backup and recovery procedures
- [ ] Create runbook for common operations

**Files to Create:**
- `deploy/kubernetes/deployment.yaml`
- `deploy/kubernetes/service.yaml`
- `deploy/kubernetes/configmap.yaml`
- `deploy/kubernetes/hpa.yaml`
- `deploy/helm/Chart.yaml`
- `deploy/helm/values.yaml`
- `docs/operations/scaling.md`
- `docs/operations/disaster-recovery.md`
- `docs/operations/runbook.md`

---

## Phase 10: Client SDKs & CLI

**Duration:** 3 weeks  
**Dependencies:** Phase 2 (can run parallel to Phases 3-9)

### 10.1 JavaScript/TypeScript SDK

**Week 20: TypeScript SDK Implementation**

**Tasks:**
- [ ] Initialize npm package (`qhronos-client`)
- [ ] Create TypeScript project structure
- [ ] Implement base client class with authentication
- [ ] Implement event resource methods (CRUD)
- [ ] Implement job resource methods (get, list, children, logs)
- [ ] Implement workflow resource methods (CRUD, execute)
- [ ] Implement script resource methods (CRUD, execute)
- [ ] Implement integration resource methods (CRUD)
- [ ] Implement project resource methods (CRUD, tokens)
- [ ] Add helper methods (waitForJob, pollJob)
- [ ] Add request/response interceptors
- [ ] Add retry logic with exponential backoff
- [ ] Add TypeScript type definitions
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Publish to npm

**Files to Create:**
- `qhronos-js-sdk/src/client.ts`
- `qhronos-js-sdk/src/resources/events.ts`
- `qhronos-js-sdk/src/resources/jobs.ts`
- `qhronos-js-sdk/src/resources/workflows.ts`
- `qhronos-js-sdk/src/resources/scripts.ts`
- `qhronos-js-sdk/src/resources/integrations.ts`
- `qhronos-js-sdk/src/resources/projects.ts`
- `qhronos-js-sdk/src/types/index.ts`
- `qhronos-js-sdk/src/utils/retry.ts`
- `qhronos-js-sdk/src/utils/interceptors.ts`
- `qhronos-js-sdk/package.json`
- `qhronos-js-sdk/tsconfig.json`
- `qhronos-js-sdk/README.md`

### 10.2 Python SDK

**Week 21: Python SDK Implementation**

**Tasks:**
- [ ] Initialize Python package (`qhronos-client`)
- [ ] Create Python project structure (setuptools/pip)
- [ ] Implement base client class with authentication
- [ ] Implement event resource methods (CRUD)
- [ ] Implement job resource methods (get, list, children, logs)
- [ ] Implement workflow resource methods (CRUD, execute)
- [ ] Implement script resource methods (CRUD, execute)
- [ ] Implement integration resource methods (CRUD)
- [ ] Implement project resource methods (CRUD, tokens)
- [ ] Add async client support (AsyncQhronosClient)
- [ ] Add helper methods (wait_for_job, poll_job)
- [ ] Add request/response interceptors
- [ ] Add retry logic with exponential backoff
- [ ] Add Pydantic models for type safety
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Publish to PyPI

**Files to Create:**
- `qhronos-python-sdk/src/qhronos/client.py`
- `qhronos-python-sdk/src/qhronos/resources/events.py`
- `qhronos-python-sdk/src/qhronos/resources/jobs.py`
- `qhronos-python-sdk/src/qhronos/resources/workflows.py`
- `qhronos-python-sdk/src/qhronos/resources/scripts.py`
- `qhronos-python-sdk/src/qhronos/resources/integrations.py`
- `qhronos-python-sdk/src/qhronos/resources/projects.py`
- `qhronos-python-sdk/src/qhronos/models.py`
- `qhronos-python-sdk/src/qhronos/utils/retry.py`
- `qhronos-python-sdk/src/qhronos/utils/interceptors.py`
- `qhronos-python-sdk/pyproject.toml`
- `qhronos-python-sdk/README.md`

### 10.3 CLI Tool

**Week 22: CLI Implementation**

**Tasks:**
- [ ] Initialize CLI project (Node.js or Go)
- [ ] Implement CLI framework (Commander.js or Cobra)
- [ ] Implement configuration management (`~/.qhronos/config.yaml`)
- [ ] Implement authentication handling
- [ ] Implement events commands (create, get, list, update, delete, jobs)
- [ ] Implement jobs commands (get, list, children, logs, watch, wait)
- [ ] Implement workflows commands (create, get, list, update, delete, execute, jobs)
- [ ] Implement scripts commands (create, get, list, update, delete, execute, jobs)
- [ ] Implement integrations commands (create, get, list, update, delete)
- [ ] Implement projects commands (create, get, list, update, tokens)
- [ ] Implement system commands (status, schedules)
- [ ] Add colored output with tables
- [ ] Add JSON/YAML output formats
- [ ] Add command completion (bash/zsh/fish)
- [ ] Add streaming output for watch commands
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Build standalone binaries (Linux, macOS, Windows)
- [ ] Publish to npm/PyPI/GitHub Releases

**Files to Create:**
- `qhronos-cli/src/index.ts` (or `cmd/qhronos/main.go`)
- `qhronos-cli/src/commands/events.ts`
- `qhronos-cli/src/commands/jobs.ts`
- `qhronos-cli/src/commands/workflows.ts`
- `qhronos-cli/src/commands/scripts.ts`
- `qhronos-cli/src/commands/integrations.ts`
- `qhronos-cli/src/commands/projects.ts`
- `qhronos-cli/src/commands/system.ts`
- `qhronos-cli/src/utils/config.ts`
- `qhronos-cli/src/utils/output.ts`
- `qhronos-cli/src/utils/auth.ts`
- `qhronos-cli/package.json` (or `go.mod`)
- `qhronos-cli/README.md`

---

## Implementation Timeline

```
Week 1-3:   Phase 1 - Core System Refactoring
Week 4-5:   Phase 2 - API Updates & Testing
Week 6-8:   Phase 3 - Workflow System
Week 9-11:  Phase 4 - Script System
Week 12-13: Phase 5 - Integration System
Week 14:    Phase 6 - File System
Week 15:    Phase 7 - Observability & Metrics
Week 16-17: Phase 8 - Cleanup, Retention & Audit Trail
Week 18-19: Phase 9 - Scalability & Resilience
Week 20-22: Phase 10 - Client SDKs & CLI
```

### Parallel Execution Opportunities

Some phases can be executed in parallel:

```
                    Week: 1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22
Phase 1 (Core):          ████████████
Phase 2 (API):                       ██████
Phase 3 (Workflow):                        ████████████
Phase 4 (Script):                             ████████████████
Phase 5 (Integration):                                    ██████████
Phase 6 (Files):                                                ████
Phase 7 (Observability):          [Can start after Phase 2] ─────────────────████
Phase 8 (Cleanup+Audit):                                                    ████████
Phase 9 (Scalability):   [Can start after Phase 2] ──────────────────────────────────████████
Phase 10 (SDK+CLI):     [Can start after Phase 2] ──────────────────────────────────────────███████████
```

With parallel execution, estimated completion: **19 weeks** (instead of 22)

Phase 9 can run in parallel with Phases 3-8 since it focuses on infrastructure and doesn't depend on feature implementation.

Phase 10 can start after Phase 2 (API) since it only depends on the API endpoints being stable. It can run in parallel with Phases 3-9.

---

## Effort Estimation

| Phase | Component | Duration | Dependencies |
|-------|-----------|----------|--------------|
| 1 | Core System Refactoring | 3 weeks | None |
| 2 | API Updates & Testing | 2 weeks | Phase 1 |
| 3 | Workflow System | 3 weeks | Phase 2 |
| 4 | Script System | 3 weeks | Phase 3 (partial) |
| 5 | Integration System | 2 weeks | Phase 4 |
| 6 | File System | 1 week | Phase 5 |
| 7 | Observability & Metrics | 1 week | Phase 2 |
| 8 | Cleanup, Retention & Audit | 2 weeks | Phase 6 |
| 9 | Scalability & Resilience | 2 weeks | Phase 2 |
| 10 | Client SDKs & CLI | 3 weeks | Phase 2 |
| **Total** | | **22 weeks** (19 with parallel) | |

---

## Success Criteria

### Phase 1: Core System
- [ ] Project system implemented (projects table, tokens)
- [ ] JWT token generation and validation working
- [ ] Project-scoped resource isolation working
- [ ] `occurrences` table renamed to `jobs`
- [ ] `project_id` added to all major tables
- [ ] Hierarchical job structure working
- [ ] Archival tables removed
- [ ] Events deleted on completion/expiration

### Phase 2: API Updates
- [ ] `/jobs` endpoints working
- [ ] Hierarchical job queries working
- [ ] All tests passing
- [ ] Migration script validated

### Phase 3: Workflow System
- [ ] Workflow CRUD working
- [ ] Sequential and parallel execution working
- [ ] Conditional branching working
- [ ] Loop execution working (while, foreach)
- [ ] Variable system working
- [ ] Template resolution working
- [ ] Sub-workflow execution working
- [ ] Workflow API endpoints working

### Phase 4: Script System
- [ ] Script CRUD working
- [ ] Goja runtime execution working
- [ ] Module system working (`require()`)
- [ ] Built-in modules working (crypto, uuid, validator, jsonpath)
- [ ] Fetch API working
- [ ] Console API working
- [ ] Script action executor working
- [ ] `POST /scripts/{id}/execute` working

### Phase 5: Integration System
- [ ] Integration CRUD working
- [ ] LLM integrations working (OpenAI, Anthropic, Gemini, OpenRouter)
- [ ] Notification integrations working (SES, Twilio, Slack)
- [ ] Database integrations working (MySQL, PostgreSQL)
- [ ] Script modules working (`require('llm')`, `require('db')`)

### Phase 6: File System
- [ ] Object storage connection working
- [ ] File operations working (read, write, list, delete)
- [ ] File scopes working (global, workflow, event, job)
- [ ] `require('files')` module working

### Phase 7: Observability
- [ ] `/metrics` endpoint working
- [ ] `/ready` endpoint working
- [ ] HTTP metrics implemented
- [ ] Business metrics implemented
- [ ] Infrastructure metrics implemented
- [ ] Grafana dashboards created

### Phase 8: Cleanup, Retention & Audit Trail
- [ ] Audit log table created and indexed
- [ ] Async audit writer with buffered channel working
- [ ] JWT claims (user_id, token_id, role) captured in audit logs
- [ ] All CRUD operations audited (events, workflows, scripts, integrations)
- [ ] Sensitive field redaction working
- [ ] Audit log API endpoints working (`/admin/audit-logs`)
- [ ] Audit metrics implemented
- [ ] Retention policies configurable (including audit logs and logs)
- [ ] Cleanup scheduler running
- [ ] Event/schedule/job cleanup working
- [ ] Logs cleanup working (level-based retention)
- [ ] File cleanup working
- [ ] Audit log cleanup working (category-based retention)
- [ ] Admin API endpoints working
- [ ] Cleanup metrics implemented

### Phase 9: Scalability & Resilience
- [ ] Distributed locking for Expander working
- [ ] Atomic job claiming for Dispatcher working
- [ ] Workflow job queue with reliability working
- [ ] Leader election for Cleanup working
- [ ] Circuit breakers for all external dependencies working
- [ ] Retry strategies with exponential backoff working
- [ ] Graceful shutdown with connection draining working
- [ ] Stalled job detection and recovery working
- [ ] PostgreSQL read replica support working
- [ ] Redis Sentinel support working

### Phase 10: Client SDKs & CLI
- [ ] JavaScript/TypeScript SDK published to npm
- [ ] Python SDK published to PyPI
- [ ] CLI tool published (npm/PyPI/GitHub Releases)
- [ ] All SDK methods working (events, jobs, workflows, scripts, integrations, projects)
- [ ] CLI commands working (events, jobs, workflows, scripts, integrations, projects)
- [ ] SDK helper methods working (waitForJob, pollJob)
- [ ] CLI watch/wait commands working
- [ ] TypeScript types complete and accurate
- [ ] Python Pydantic models complete and accurate
- [ ] CLI configuration file support working
- [ ] CLI command completion working
- [ ] SDK unit tests passing
- [ ] CLI unit tests passing
- [ ] `/ready` endpoint with dependency health checks working
- [ ] Idempotency key support for API working
- [ ] Kubernetes manifests and Helm chart created
- [ ] Horizontal Pod Autoscaler configured
- [ ] Operations documentation complete

---

## Risk Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Data loss during migration | High | Low | Backup before migration, staged rollout, rollback scripts |
| Breaking API changes | Medium | Medium | API versioning, deprecation notices, client SDK updates |
| Performance degradation | Medium | Medium | Load testing, query optimization, connection pooling |
| Script runtime security | High | Medium | Sandboxing, resource limits, timeout enforcement |
| Integration failures | Medium | Medium | Retry logic, circuit breakers, health checks |
| Storage quota exhaustion | Medium | Low | Monitoring, alerts, cleanup policies |
| Single point of failure | High | Medium | HA configuration, multi-instance deployment |
| Split brain scenarios | High | Low | Distributed locking, leader election, idempotency |
| Cascading failures | High | Medium | Circuit breakers, bulkheads, graceful degradation |

---

## Notes

- Jobs serve as the permanent audit trail (never deleted by default)
- Workflows are stored as jobs with `type='workflow'` (no separate workflow_instances table)
- All script operations are synchronous within the Goja runtime
- Workflow execution is asynchronous via Redis queue
- Integrations store encrypted credentials in the database
- File cleanup follows retention policies based on scope
- Observability and Scalability can be implemented in parallel with other phases
- Multi-instance deployment requires Redis for coordination
- All background workers are designed to be horizontally scalable
- Idempotency is critical for at-least-once delivery guarantees
