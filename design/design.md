# Qhronos Design Document

## 1. Introduction

Qhronos is a developer-first, event scheduling and workflow orchestration platform. It enables clients to schedule one-time or recurring events via a simple REST API, reliably deliver webhooks, and orchestrate complex multi-step workflows with conditional logic, loops, and AI capabilities. Qhronos is designed for reliability, scalability, and extensibility, making it suitable for both cloud and on-premise deployments.

**Core Use Cases:**
- Scheduling time-based notifications or reminders
- Automating webhook calls for recurring business processes
- Building workflow triggers based on time or recurrence rules
- Orchestrating multi-step automation workflows
- AI-powered agentic workflows with iterative reasoning
- Data processing pipelines with conditional logic

**Value Proposition:**
- Durable, auditable job and log tracking (PostgreSQL-backed)
- Simple, intuitive JSON APIs
- Secure, role-based access control and token management
- Reliable, retryable webhook delivery
- Powerful workflow orchestration with scripts and LLM integration
- Modular, stateless, and scalable architecture
- Embeddable as a Go library

---

## 1.1 Repository Structure

Qhronos is organized as a monorepo with the following structure:

```
qhronos/                          # Root monorepo
├── design/                       # Design documents
│   ├── design.md                 # Main design document (this file)
│   ├── workflow-design.md        # Workflow system design
│   ├── script-design.md          # Script execution design
│   └── client-design.md          # Client SDK design
├── plans/                        # Implementation plans
│   ├── plan.md                   # Phased implementation plan
│   └── gap-analysis.md           # Gap analysis document
├── qhronos-server/               # Go backend server
│   ├── internal/                 # Internal packages
│   ├── pkg/                      # Public packages (embeddable library)
│   ├── migrations/               # Database migrations
│   ├── docs/                     # API and embedding documentation
│   ├── main.go                   # Server entry point
│   ├── go.mod                    # Go module definition
│   └── ...
├── qhronos-js-sdk/               # JavaScript/TypeScript SDK
│   ├── src/                      # Source code
│   ├── package.json              # npm package definition
│   └── ...
├── qhronos-python-sdk/           # Python SDK
│   ├── src/qhronos/              # Source code
│   ├── pyproject.toml            # Python package definition
│   └── ...
└── README.md                     # Monorepo README
```

---

## 2. System Overview

### High-Level Architecture Diagram

```
[Client/API Consumer]
       │
       ▼
   [API Layer (Gin)]
       │
       ▼
   [Handlers]
       │
       ▼
   [Services] <─────────────┐
       │                    │
       ▼                    │
   [Repositories]           │
       │                    │
       ▼                    │
   [Database (Postgres)]    │
                            │
   [Middleware]─────────────┘
       │
       ▼
   [Scheduler Layer] ──► [Redis (Schedules)]
       │ (Core Scheduler, Expander, Dispatcher, Cleanup)
       ▼
   [Background Jobs: Expander, Dispatcher, Cleanup]
       │
       ▼
   [Action System] ──► [Webhook/WebSocket/API Call/Script/Integration]
       │                      │
       │                      ▼
       │              [Integrations] ──► [LLM Providers/Notification Channels]
       │
       ▼
   [Workflow Engine] ──► [Step Executor] ──► [Object Storage (MinIO/S3)]
       │
       ▼
   [Jobs (with status)] ──► [PostgreSQL]
```

### Component Summary Table

| Component         | Responsibility                                              |
|-------------------|------------------------------------------------------------|
| API Layer         | HTTP endpoints, routing, middleware wiring                  |
| Handlers          | Request validation, business logic orchestration            |
| Services          | Business logic, token/HMAC, scheduling logic                |
| Repositories      | Data access (sqlx), persistence                            |
| Database          | PostgreSQL, durable storage for events/jobs/workflows |
| Middleware        | Logging, error handling, authentication, rate limiting      |
| Scheduler Layer   | Expander, Dispatcher, Cleanup (background jobs)             |
| Redis             | Schedules (temporary scheduled executions), rate limiting, background job coordination |
| Action System     | Extensible action execution (webhook, websocket, apicall, script, integration) |
| Integrations      | External service connectors (LLM providers, notification channels) |
| Workflow Engine   | Multi-step workflow orchestration and state management      |
| Script Runtime    | JavaScript execution engine (Goja) for workflow scripts     |
| Object Storage    | File storage (MinIO/S3 compatible) for global and workflow files |
| Jobs              | Persistent execution records with status, serve as audit trail (hierarchical: job → workflow → step → action) |

---

## 3. Key Concepts

### Events
An **Event** is a user-defined action or reminder, scheduled to occur at a specific time or on a recurring basis. Each event contains metadata, an action configuration (webhook, websocket, apicall, script, llm, or workflow), and optional recurrence rules.

**Event Lifecycle:**
- Events are created and stored in the database
- For one-time events: Event is deleted after the job completes (successfully or after max retries)
- For recurring events: Event is deleted when recurrence expires (no more occurrences to generate)
- Only jobs are retained for audit purposes

### Schedules
A **Schedule** represents a scheduled execution that is waiting to run. Schedules are stored in Redis and are temporary - they are removed once executed or expired.

**Schedule Lifecycle:**
- Schedules are created when events are scheduled (by the Expander)
- Schedules are stored in Redis with execution time
- When due, schedules are picked up by the Dispatcher
- Upon execution, a Job is created in PostgreSQL
- Schedules are removed from Redis after execution

### Jobs
A **Job** represents an actual execution record with status. Jobs are stored in PostgreSQL and serve as the audit trail. Jobs are never deleted.

**Job Structure:**
- **General Fields**: id, schedule_id (if from schedule), type, status, started_at, completed_at, duration_ms, error_message, parent_job_id
- **Type-Specific Fields**: Stored in JSONB `data` field

**Job Types:**
- **job**: Top-level job execution (from event or workflow execution)
- **workflow**: Workflow execution job (contains workflow details)
- **step**: Workflow step execution job (contains step details)
- **api_call**: API call action execution job
- **script**: Script action execution job
- **webhook**: Webhook action execution job
- **websocket**: WebSocket action execution job
- **integration**: Integration action execution job (LLM, notification channel, etc.)

**Job Hierarchy:**
- Job → Workflow → Step → Action jobs
- Parent-child relationships via `parent_job_id`
- Step jobs are created after action jobs complete

**Job Lifecycle:**
- Jobs are created when schedules are executed or workflows are triggered
- Jobs track execution status (pending, running, completed, failed, cancelled)
- Jobs persist indefinitely for auditing

### Workflows
A **Workflow** is a reusable definition of steps and their execution logic. Workflows enable complex automation with sequential and parallel execution, conditional branching, loops, and sub-workflows.

**Workflow Execution:**
- Workflows can be executed directly (creates a job) or scheduled (creates a schedule that later creates a job)
- Each workflow execution creates a job with `type` set to `workflow`
- The workflow job tracks the workflow's state, variables, and step execution history
- Step jobs are created for each step execution within the workflow job

### Steps
A **Step** is a single unit of work in a workflow. Supported step types:
- **Action**: Executes an action (webhook, websocket, apicall, script, integration, workflow)
- **Condition**: Evaluates JavaScript-like expressions for branching
- **Set Variable**: Sets or updates workflow-level variables
- **Delay**: Waits for a specified duration
- **Loop**: Iterates over items or repeats until a condition is met
- **Sub-workflow**: Executes another workflow as a step

### Scripts
**Scripts** are JavaScript code stored in a repository that can be executed within workflow steps. Scripts have access to:
- Input data and previous step outputs
- Workflow variables
- Database operations via database integrations (MySQL/PostgreSQL)
- LLM API calls via LLM integrations
- File operations (object storage)
- HTTP requests via fetch API

### Actions
An **Action** defines how an event or workflow step is executed. Supported action types:
- **webhook**: Delivers event to HTTP endpoint
- **websocket**: Delivers event to connected WebSocket client
- **apicall**: Makes generic HTTP request with custom method, headers, body
- **script**: Executes JavaScript code from scripts repository
- **integration**: Uses an integration (LLM, notification channel, etc.)
- **workflow**: Triggers another workflow

### Integrations
**Integrations** are external service connectors that can be used within actions. Integration types:

**LLM Integrations:**
- **openai**: OpenAI API (GPT-3.5, GPT-4, etc.)
- **anthropic**: Anthropic Claude API
- **gemini**: Google Gemini API
- **openrouter**: OpenRouter API (multi-provider)

**Notification Channel Integrations:**
- **ses**: Amazon SES (Simple Email Service) for email delivery
- **twilio**: Twilio for SMS and voice calls
- **slack**: Slack webhook integration
- **discord**: Discord webhook integration
- **telegram**: Telegram Bot API

**Database Integrations:**
- **mysql**: MySQL database connection
- **postgres**: PostgreSQL database connection

**Spreadsheet Integrations:**
- **google_sheets**: Google Sheets API for reading, writing, and manipulating spreadsheet data

Integrations are configured separately and referenced by ID in actions and scripts. This allows:
- Centralized credential management
- Reuse across multiple actions and scripts
- Easy credential rotation
- Provider-specific configuration
- Secure credential storage with encryption


### Webhook Delivery
When a job is due, Qhronos delivers a webhook (HTTP POST) to the event's configured URL. Delivery is signed (HMAC) for security and retried on failure according to policy. Each attempt is logged.

### Scheduling & Recurrence
Qhronos supports both one-time and recurring events. Recurrence is defined using iCalendar (RFC 5545) rules. The scheduler expands recurring events into individual schedules (stored in Redis) within a configurable lookahead window. When schedules are due, they are executed and create jobs in PostgreSQL.

### Authentication & Authorization
Qhronos uses JWT tokens and a master token for API authentication. Access control is enforced via token scopes and roles, ensuring secure, multi-tenant operation.

---

## 4. Core Features

### 4.1 Event Scheduling

**One-Time Events:**
- Schedule events to execute at a specific time
- Simple JSON API for creation and management
- Automatic job generation
- Event deleted after job completes

**Recurring Events:**
- Support for iCalendar RFC 5545 recurrence rules
- Daily, weekly, monthly, yearly frequencies
- Custom intervals and by-day/by-date rules
- Configurable lookahead window for job expansion
- Event deleted when recurrence expires

**Event Management:**
- Create, read, update, delete events via REST API
- Tag-based filtering and organization
- Metadata support for custom data
- Status tracking (active, inactive)
- Automatic cleanup when events are done

### 4.2 Action System

**Extensible Action Types:**
- **Webhook**: HTTP POST delivery to configured URL
- **WebSocket**: Real-time delivery to connected clients
- **API Call**: Generic HTTP requests with full control
- **Script**: JavaScript code execution
- **LLM**: Large Language Model API calls (OpenAI, Anthropic, Gemini, OpenRouter)
- **DB**: Database queries (MySQL, PostgreSQL) via integration
- **Spreadsheet**: Google Sheets read/write via integration
- **Notification**: Send notifications via channels (email, SMS, Slack, Discord, Telegram)
- **Workflow**: Trigger other workflows

**Integration Types:**
- **LLM Integrations**: OpenAI, Anthropic, Gemini, OpenRouter
- **Notification Channels**: Amazon SES (email), Twilio (SMS/voice), Slack, Discord, Telegram
- **Database Integrations**: MySQL, PostgreSQL
- **Spreadsheet Integrations**: Google Sheets

**Action Configuration:**
- Type-specific parameters
- Timeout configuration per action
- Retry strategies with exponential backoff
- Error handling and failure paths
- Execution logging for all attempts

### 4.3 WebSocket Real-Time Delivery

**Connection Types:**
- **Client-Hook Listener**: Receives events for specific client hooks (`q:<client-name>`)
- **Tag-Based Listener**: Receives events matching specified tags

**Features:**
- Real-time event delivery
- Acknowledgment support for client-hook connections
- Authentication via JWT or master token
- Automatic reconnection handling

### 4.4 Workflow System

**Multi-Step Execution:**
- Sequential step execution
- Parallel step execution
- Conditional branching based on step outputs
- Loop constructs (while, foreach)
- Sub-workflow composition

**State Management:**
- Durable workflow state in PostgreSQL
- Workflow-level variables for data sharing
- Step execution history and outputs
- Error state tracking

**Variable System:**
- Global workflow variables
- Variable assignment via Set Variable step
- Variable assignment via script output
- Template variable resolution in actions
- JavaScript-like condition evaluation

**Step Types:**
- **Action Step**: Execute webhook, websocket, apicall, script, or llm actions
- **Condition Step**: Branch based on JavaScript-like expressions
- **Set Variable Step**: Set or update workflow variables
- **Delay Step**: Wait for specified duration
- **Loop Step**: Iterate over items or repeat until condition
- **Sub-workflow Step**: Execute another workflow

**Error Handling:**
- Per-step retry configuration
- Error handlers for failed steps
- Timeout handling with configurable timeouts
- Failure path routing

**Logging:**
- Step jobs for all steps
- Input/output data logging
- Error logging with stack traces
- Duration tracking
- Loop iteration logging

### 4.5 Script System

**JavaScript Execution:**
- Sandboxed Goja runtime
- Synchronous execution model
- Direct access to context (input, steps, workflow, console)
- Standard JavaScript features (ES5+)

**Built-in APIs:**
- **fetch**: Synchronous HTTP requests
- **db**: Database operations (MySQL/PostgreSQL)
- **llm**: LLM API calls (OpenAI, Anthropic, Gemini, OpenRouter)
- **files**: File operations (object storage: MinIO/S3 compatible)
- **crypto**: Cryptographic functions
- **uuid**: UUID generation
- **validator**: Data validation
- **jsonpath**: JSON path queries

**Script Repository:**
- Versioned script storage
- Script CRUD operations via API
- Script execution within workflow steps
- Input/output data passing

**Logging:**
- Script jobs for all script runs
- Input/output data logging
- Error logging with stack traces
- Duration tracking
- Variable assignment logging

**File Operations:**
- **Global Files**: Accessible across all workflows (`global/path/to/file.txt`)
- **Workflow Files**: Scoped to workflow job (`workflow/path/to/file.txt`)
- Read/write text, JSON, and binary files
- List and delete files
- File metadata access

**Database Operations:**
- Query execution (SELECT)
- Data modification (INSERT, UPDATE, DELETE)
- Transaction support (begin, commit, rollback)
- Parameterized queries for security

**LLM Integration:**
- Multi-provider support (OpenAI, Anthropic, Gemini, OpenRouter)
- Standardized request/response format
- Token usage tracking
- Streaming support (optional)
- Temperature and max_tokens configuration

### 4.6 Authentication & Authorization

**Token Types:**
- **Master Token**: Static API key with full access (for system administration)
- **Project Token**: JWT token scoped to a specific project

**Access Control:**
- Project-based isolation (all resources belong to a project)
- Role-based access within project (read, write, admin)
- Scope-based filtering (tags)
- Token expiration support
- Secure token generation and validation

**Security Features:**
- HMAC signing for webhook deliveries
- Rate limiting per project/token
- Audit logging for all operations
- Secure token storage

### 4.6.1 Project System

Projects provide multi-tenancy without user management. Each project is an isolated namespace for all resources.

**Project Table Schema:**
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,  -- URL-friendly identifier
    description TEXT,
    settings JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deleted')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_projects_slug ON projects(slug);
CREATE INDEX idx_projects_status ON projects(status);
```

**Project Settings (JSONB):**
```json
{
  "rate_limit": {
    "requests_per_minute": 1000,
    "requests_per_day": 100000
  },
  "retention": {
    "jobs": "90d",
    "audit_logs": "365d"
  },
  "features": {
    "workflows_enabled": true,
    "scripts_enabled": true,
    "integrations_enabled": true,
    "llm_enabled": true
  },
  "quotas": {
    "max_events": 10000,
    "max_workflows": 100,
    "max_scripts": 100,
    "max_integrations": 50
  },
  "webhooks": {
    "allowed_domains": ["*.example.com"],
    "hmac_secret": "project-specific-secret"
  }
}
```

**Project API Endpoints:**

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/projects` | Create new project | Master Token |
| GET | `/projects` | List all projects | Master Token |
| GET | `/projects/:id` | Get project details | Master Token |
| PATCH | `/projects/:id` | Update project | Master Token |
| DELETE | `/projects/:id` | Soft delete project | Master Token |
| POST | `/projects/:id/tokens` | Generate project token | Master Token |
| GET | `/projects/:id/tokens` | List project tokens | Master Token |
| DELETE | `/projects/:id/tokens/:token_id` | Revoke token | Master Token |

**Project Token Generation:**
```
POST /projects/:id/tokens
{
  "name": "Production API Key",
  "role": "write",
  "scopes": ["events:*", "workflows:*", "jobs:read"],
  "expires_at": "2025-12-31T23:59:59Z"  // Optional, null = never expires
}
```

**Response:**
```json
{
  "token_id": "tok_abc123",
  "token": "qhr_proj_eyJhbGciOiJIUzI1NiIs...",  // JWT, only shown once
  "name": "Production API Key",
  "role": "write",
  "scopes": ["events:*", "workflows:*", "jobs:read"],
  "expires_at": "2025-12-31T23:59:59Z",
  "created_at": "2024-01-15T10:00:00Z"
}
```

**Project Tokens Table:**
```sql
CREATE TABLE project_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,  -- SHA256 hash of token
    role VARCHAR(50) NOT NULL CHECK (role IN ('read', 'write', 'admin')),
    scopes TEXT[] NOT NULL DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE,  -- NULL = never expires
    last_used_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_project_tokens_project_id ON project_tokens(project_id);
CREATE INDEX idx_project_tokens_token_hash ON project_tokens(token_hash);
```

### 4.6.2 JWT Token Structure

**Project JWT Token:**
```json
{
  "iss": "qhronos",                    // Issuer
  "aud": "qhronos-api",                // Audience
  "iat": 1703001600,                   // Issued at
  "exp": 1703088000,                   // Expiration (optional)
  "jti": "tok_abc123",                 // Token ID (for revocation)
  "pid": "proj_xyz789",                // Project ID (required)
  "role": "write",                     // Access role (read, write, admin)
  "scopes": ["events:*", "jobs:read"], // Permission scopes
  "sub": "api-key"                     // Subject (always "api-key" for project tokens)
}
```

**Token Claims:**

| Claim | Description | Required |
|-------|-------------|----------|
| `iss` | Issuer (always "qhronos") | Yes |
| `aud` | Audience (always "qhronos-api") | Yes |
| `iat` | Issued at timestamp | Yes |
| `exp` | Expiration timestamp | No (null = never) |
| `jti` | Token ID (unique identifier) | Yes |
| `pid` | Project ID | Yes |
| `role` | Access role | Yes |
| `scopes` | Permission scopes array | Yes |
| `sub` | Subject type | Yes |

**Roles & Permissions:**

| Role | Description | Permissions |
|------|-------------|-------------|
| `read` | Read-only access | GET on all resources |
| `write` | Read + Write access | GET, POST, PUT, PATCH on resources |
| `admin` | Full project access | All operations including DELETE |

**Scopes:**
```
events:read      - Read events
events:write     - Create/update events
events:delete    - Delete events
events:*         - All event operations

workflows:read   - Read workflows
workflows:write  - Create/update/execute workflows
workflows:delete - Delete workflows
workflows:*      - All workflow operations

scripts:read     - Read scripts
scripts:write    - Create/update/execute scripts
scripts:delete   - Delete scripts
scripts:*        - All script operations

jobs:read        - Read logs
jobs:*           - All job operations (including cancel/retry)

integrations:read   - Read integrations
integrations:write  - Create/update integrations
integrations:delete - Delete integrations
integrations:*      - All integration operations
```

### 4.6.3 Resource Isolation

All resources are scoped to a project. The `project_id` is added to all major tables:

```sql
-- Events scoped to project
ALTER TABLE events ADD COLUMN project_id UUID NOT NULL REFERENCES projects(id);
CREATE INDEX idx_events_project_id ON events(project_id);

-- Workflows scoped to project
ALTER TABLE workflows ADD COLUMN project_id UUID NOT NULL REFERENCES projects(id);
CREATE INDEX idx_workflows_project_id ON workflows(project_id);

-- Scripts scoped to project
ALTER TABLE scripts ADD COLUMN project_id UUID NOT NULL REFERENCES projects(id);
CREATE INDEX idx_scripts_project_id ON scripts(project_id);

-- Integrations scoped to project
ALTER TABLE integrations ADD COLUMN project_id UUID NOT NULL REFERENCES projects(id);
CREATE INDEX idx_integrations_project_id ON integrations(project_id);

-- Jobs scoped to project
ALTER TABLE jobs ADD COLUMN project_id UUID NOT NULL REFERENCES projects(id);
CREATE INDEX idx_jobs_project_id ON jobs(project_id);

-- Audit logs scoped to project
ALTER TABLE audit_logs ADD COLUMN project_id UUID REFERENCES projects(id);
CREATE INDEX idx_audit_logs_project_id ON audit_logs(project_id);
```

**Query Isolation:**

All queries automatically filter by project_id from the JWT:

```go
// Middleware extracts project_id from JWT
func ProjectMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        claims := r.Context().Value("claims").(*JWTClaims)
        ctx := context.WithValue(r.Context(), "project_id", claims.ProjectID)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// Repository automatically filters by project_id
func (r *EventRepository) List(ctx context.Context, filters EventFilters) ([]Event, error) {
    projectID := ctx.Value("project_id").(string)
    query := r.db.Where("project_id = ?", projectID)
    // ... apply additional filters
}
```

### 4.7 Audit Trail

Comprehensive audit trail for tracking all API operations, user actions, and system events.

#### Audit Log Table

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Project & Actor Information (from JWT)
    project_id UUID REFERENCES projects(id),  -- From JWT 'pid' claim (null for master token ops)
    token_id VARCHAR(255),             -- From JWT 'jti' claim
    role VARCHAR(50),                  -- From JWT 'role' claim
    actor_type VARCHAR(50) NOT NULL,   -- 'project_token', 'master_token', 'system'
    actor_metadata JSONB,              -- Additional actor info (token name, etc.)
    
    -- Action Information
    action VARCHAR(100) NOT NULL,      -- 'event.create', 'workflow.execute', etc.
    resource_type VARCHAR(50) NOT NULL, -- 'event', 'workflow', 'script', 'integration', etc.
    resource_id VARCHAR(255),          -- ID of affected resource
    
    -- Request Details
    method VARCHAR(10),                -- HTTP method
    path VARCHAR(500),                 -- API path
    request_id VARCHAR(100),           -- Request correlation ID
    ip_address INET,                   -- Client IP
    user_agent TEXT,                   -- Client user agent
    
    -- Change Details
    before_state JSONB,                -- State before change (for updates/deletes)
    after_state JSONB,                 -- State after change (for creates/updates)
    changes JSONB,                     -- Diff of changes (computed)
    
    -- Result
    status VARCHAR(50) NOT NULL,       -- 'success', 'failure', 'error'
    error_message TEXT,                -- Error details if failed
    duration_ms INTEGER,               -- Operation duration
    
    -- Indexing support
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_audit_logs_tenant_id ON audit_logs(tenant_id) WHERE tenant_id IS NOT NULL;
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_status ON audit_logs(status);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Partitioning for performance (PostgreSQL 12+)
-- Consider partitioning by month for large deployments
```

#### Audited Actions

| Category | Actions |
|----------|---------|
| **Events** | `event.create`, `event.update`, `event.delete`, `event.pause`, `event.resume`, `event.trigger` |
| **Jobs** | `job.cancel`, `job.retry`, `job.view` |
| **Workflows** | `workflow.create`, `workflow.update`, `workflow.delete`, `workflow.execute` |
| **Scripts** | `script.create`, `script.update`, `script.delete`, `script.execute` |
| **Integrations** | `integration.create`, `integration.update`, `integration.delete`, `integration.test` |
| **Tokens** | `token.create`, `token.revoke`, `token.list` |
| **Admin** | `admin.cleanup.trigger`, `admin.retention.update`, `admin.config.update` |
| **Auth** | `auth.login`, `auth.logout`, `auth.token.refresh`, `auth.failed` |

#### Audit Log Entry Example

```json
{
  "id": "audit-123-uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "project_id": "proj-abc-uuid",
  "token_id": "tok_xyz789",
  "role": "write",
  "actor_type": "project_token",
  "actor_metadata": {
    "token_name": "Production API Key"
  },
  "action": "event.create",
  "resource_type": "event",
  "resource_id": "event-xyz-uuid",
  "method": "POST",
  "path": "/events",
  "request_id": "req-123-uuid",
  "ip_address": "192.168.1.100",
  "user_agent": "QhronosClient/1.0",
  "before_state": null,
  "after_state": {
    "id": "event-xyz-uuid",
    "name": "Daily Report",
    "status": "active"
  },
  "changes": null,
  "status": "success",
  "error_message": null,
  "duration_ms": 45
}
```

#### Performance Considerations

**Asynchronous Logging:**
- Audit logs are written asynchronously to avoid impacting API response times
- Uses buffered channel with configurable buffer size (default: 10,000)
- Background worker batch-inserts logs to database
- Graceful shutdown ensures all pending logs are flushed

```
[API Handler] ──► [Audit Buffer Channel] ──► [Audit Writer Worker] ──► [PostgreSQL]
                      (10k buffer)              (batch insert)
```

**Buffered Writer Configuration:**
```yaml
audit:
  enabled: true
  buffer_size: 10000          # Channel buffer size
  batch_size: 100             # Logs per batch insert
  flush_interval: 1s          # Max time between flushes
  async: true                 # Async mode (recommended)
  include_request_body: false # Don't log request bodies (performance)
  include_response_body: false # Don't log response bodies (performance)
  sensitive_fields:           # Fields to redact
    - password
    - api_key
    - secret
    - token
    - credentials
```

**Sampling for High-Volume Operations:**
```yaml
audit:
  sampling:
    enabled: true
    rules:
      - action: "job.view"
        rate: 0.1           # Log 10% of job.view operations
      - action: "event.list"
        rate: 0.01          # Log 1% of event.list operations
      - action: "*"
        rate: 1.0           # Log 100% of all other operations
```

#### Audit Log Retention & Cleanup

**Retention Configuration:**
```yaml
retention:
  audit_logs:
    default: 365d           # Default audit log retention (1 year)
    auth: 730d              # Auth-related logs (2 years for compliance)
    admin: 730d             # Admin action logs (2 years)
    sensitive: 730d         # Sensitive operations (2 years)
  cleanup:
    audit_interval: 24h     # Cleanup runs daily
    audit_batch_size: 10000 # Records per cleanup batch
```

**Retention Policy Table:**

| Audit Category | Default Retention | Configurable | Compliance Notes |
|----------------|-------------------|--------------|------------------|
| Auth Events | 730 days | Yes | Required for security audits |
| Admin Actions | 730 days | Yes | Required for compliance |
| Create/Delete Operations | 365 days | Yes | Data governance |
| Update Operations | 365 days | Yes | Change tracking |
| Read Operations | 90 days | Yes | Lower priority, high volume |
| Failed Operations | 365 days | Yes | Security monitoring |

**Cleanup Process:**
```
Audit Cleanup Scheduler
    ├── Runs every: 24 hours (configurable)
    ├── Batch size: 10,000 records per iteration
    └── Process:
        1. Identify logs past retention period
        2. Optional: Archive to S3/GCS before deletion
        3. Delete in batches (avoid table locks)
        4. Update cleanup metrics
        5. Log cleanup summary to audit log
```

**Optional Archival:**
```yaml
audit:
  archival:
    enabled: true
    destination: "s3://qhronos-audit-archive"
    format: "json_lines"    # or "parquet" for analytics
    compress: true          # gzip compression
    partition_by: "month"   # Partition by month
```

#### Audit Log API

**List Audit Logs:**
```
GET /admin/audit-logs?project_id=xxx&action=event.create&from=2024-01-01&to=2024-01-31&limit=100
```

**Response:**
```json
{
  "data": [
    {
      "id": "audit-123-uuid",
      "timestamp": "2024-01-15T10:30:00Z",
      "project_id": "proj-abc-uuid",
      "token_id": "tok_xyz789",
      "action": "event.create",
      "resource_type": "event",
      "resource_id": "event-xyz-uuid",
      "status": "success"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 100,
    "total": 1234,
    "has_more": true
  }
}
```

**Get Audit Log Details:**
```
GET /admin/audit-logs/:id
```

**Export Audit Logs:**
```
POST /admin/audit-logs/export
{
  "from": "2024-01-01T00:00:00Z",
  "to": "2024-01-31T23:59:59Z",
  "format": "csv",
  "filters": {
    "project_id": "proj-abc-uuid",
    "action": "event.*"
  }
}
```

#### Audit Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_audit_logs_total` | Counter | `action`, `status` | Total audit log entries |
| `qhronos_audit_buffer_size` | Gauge | - | Current buffer queue size |
| `qhronos_audit_flush_duration_seconds` | Histogram | - | Time to flush audit batch |
| `qhronos_audit_logs_dropped_total` | Counter | `reason` | Dropped logs (buffer full) |
| `qhronos_audit_cleanup_records_total` | Counter | `category` | Records cleaned up |

#### Logs Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_logs_total` | Counter | `level`, `category` | Total log entries |
| `qhronos_logs_buffer_size` | Gauge | - | Current log buffer queue size |
| `qhronos_logs_flush_duration_seconds` | Histogram | - | Time to flush log batch |
| `qhronos_logs_dropped_total` | Counter | `reason` | Dropped logs (buffer full, size exceeded) |
| `qhronos_logs_bytes_total` | Counter | `category` | Total bytes of log data |
| `qhronos_logs_cleanup_records_total` | Counter | `level` | Job log records cleaned up |

### 4.8 Monitoring & Observability

**Health Endpoints:**
- `/health`: Simple health check (liveness probe)
- `/ready`: Readiness check (database, Redis connectivity)
- `/status`: Detailed service status and configuration
- `/metrics`: Prometheus metrics endpoint

**Logging:**
- Structured logging with zap
- Request/response logging
- Error tracing
- Performance metrics

**Jobs:**
- Persistent execution records for all executions
- Job jobs (top-level)
- Script jobs
- Workflow step jobs
- Queryable via `/jobs` API endpoint

### 4.9 Prometheus Metrics

Comprehensive metrics collection using Prometheus client library for Go.

**HTTP Metrics:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_http_requests_total` | Counter | `method`, `path`, `status` | Total HTTP requests |
| `qhronos_http_request_duration_seconds` | Histogram | `method`, `path` | HTTP request latency |
| `qhronos_http_requests_in_flight` | Gauge | - | Current in-flight requests |
| `qhronos_http_request_size_bytes` | Histogram | `method`, `path` | HTTP request body size |
| `qhronos_http_response_size_bytes` | Histogram | `method`, `path` | HTTP response body size |

**Event Metrics:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_events_total` | Gauge | `status` | Total events by status |
| `qhronos_events_created_total` | Counter | - | Total events created |
| `qhronos_events_deleted_total` | Counter | `reason` | Events deleted (completed, expired, manual) |

**Schedule Metrics:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_schedules_total` | Gauge | - | Current schedules in Redis |
| `qhronos_schedules_created_total` | Counter | - | Total schedules created |
| `qhronos_schedules_executed_total` | Counter | - | Total schedules executed |
| `qhronos_schedules_expired_total` | Counter | - | Total schedules expired |

**Job Metrics:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_jobs_total` | Counter | `type`, `status` | Total jobs by type and status |
| `qhronos_jobs_duration_seconds` | Histogram | `type` | Job execution duration |
| `qhronos_jobs_in_progress` | Gauge | `type` | Jobs currently running |
| `qhronos_jobs_retry_total` | Counter | `type` | Job retry attempts |

**Workflow Metrics:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_workflow_executions_total` | Counter | `workflow_id`, `status` | Workflow executions by status |
| `qhronos_workflow_execution_duration_seconds` | Histogram | `workflow_id` | Workflow execution duration |
| `qhronos_workflow_steps_total` | Counter | `workflow_id`, `step_type`, `status` | Step executions |
| `qhronos_workflow_steps_duration_seconds` | Histogram | `step_type` | Step execution duration |
| `qhronos_workflow_active` | Gauge | - | Currently active workflows |

**Script Metrics:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_script_executions_total` | Counter | `script_id`, `status` | Script executions |
| `qhronos_script_execution_duration_seconds` | Histogram | `script_id` | Script execution duration |
| `qhronos_script_memory_bytes` | Histogram | - | Script memory usage |

**Integration Metrics:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_integration_requests_total` | Counter | `type`, `provider`, `status` | Integration requests |
| `qhronos_integration_request_duration_seconds` | Histogram | `type`, `provider` | Integration request latency |
| `qhronos_integration_errors_total` | Counter | `type`, `provider`, `error_type` | Integration errors |

**LLM-Specific Metrics:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_llm_tokens_total` | Counter | `provider`, `model`, `type` | Token usage (prompt/completion) |
| `qhronos_llm_cost_dollars` | Counter | `provider`, `model` | Estimated cost |
| `qhronos_llm_request_duration_seconds` | Histogram | `provider`, `model` | LLM request latency |

**Action Metrics:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_action_executions_total` | Counter | `type`, `status` | Action executions |
| `qhronos_action_duration_seconds` | Histogram | `type` | Action execution duration |
| `qhronos_webhook_deliveries_total` | Counter | `status_code` | Webhook deliveries by status code |
| `qhronos_webhook_delivery_duration_seconds` | Histogram | - | Webhook delivery latency |

**Database Metrics:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_db_connections_total` | Gauge | `state` | Database connections (active, idle) |
| `qhronos_db_queries_total` | Counter | `operation` | Database queries |
| `qhronos_db_query_duration_seconds` | Histogram | `operation` | Query execution time |

**Redis Metrics:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_redis_commands_total` | Counter | `command` | Redis commands executed |
| `qhronos_redis_command_duration_seconds` | Histogram | `command` | Redis command latency |
| `qhronos_redis_connections` | Gauge | - | Active Redis connections |

**Object Storage Metrics:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_storage_operations_total` | Counter | `operation`, `status` | Storage operations |
| `qhronos_storage_bytes_total` | Counter | `operation` | Bytes read/written |
| `qhronos_storage_operation_duration_seconds` | Histogram | `operation` | Storage operation latency |

**Scheduler Metrics:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_scheduler_runs_total` | Counter | `component` | Scheduler component runs (expander, dispatcher, cleanup) |
| `qhronos_scheduler_run_duration_seconds` | Histogram | `component` | Scheduler run duration |
| `qhronos_scheduler_errors_total` | Counter | `component` | Scheduler errors |
| `qhronos_expander_events_processed_total` | Counter | - | Events processed by expander |
| `qhronos_dispatcher_jobs_dispatched_total` | Counter | - | Jobs dispatched |

**System Metrics:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_uptime_seconds` | Gauge | - | Service uptime |
| `qhronos_info` | Gauge | `version`, `go_version` | Build information |

**Example Prometheus Configuration:**
```yaml
scrape_configs:
  - job_name: 'qhronos'
    static_configs:
      - targets: ['qhronos:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

**Example Grafana Dashboard Panels:**
- Request rate and latency (HTTP)
- Job success/failure rates
- Workflow execution status
- Script execution performance
- Integration latency by provider
- LLM token usage and cost
- Queue depth over time
- Database and Redis health

### 4.10 Data Cleanup & Retention Management

Comprehensive cleanup and retention management system for maintaining system health and compliance.

#### Retention Policies

**Configurable Retention Periods:**

| Data Type | Default Retention | Configurable | Description |
|-----------|-------------------|--------------|-------------|
| Jobs | 90 days | Yes | Execution records (audit trail) |
| Logs | 30 days | Yes | Detailed execution logs (console, LLM, API) |
| Logs (Error) | 90 days | Yes | Error logs retained longer for debugging |
| Workflow Jobs | 90 days | Yes | Workflow execution records |
| Script Jobs | 90 days | Yes | Script execution records |
| Failed Jobs | 180 days | Yes | Failed executions for debugging |
| Audit Logs | 365 days | Yes | API operation audit trail |
| Audit Logs (Auth) | 730 days | Yes | Authentication/authorization logs |
| Audit Logs (Admin) | 730 days | Yes | Admin action logs |
| Performance Metrics | 365 days | Yes | System performance data (Prometheus) |
| Global Files | Indefinite | Yes | Shared files in object storage |
| Workflow Files | Job retention + 7 days | Yes | Workflow-scoped files |
| Job Files | Immediate | No | Deleted after job completion |
| Event Files | Event lifetime | No | Deleted when event is deleted |

**Retention Configuration:**
```yaml
retention:
  jobs:
    default: 90d          # Default job retention
    failed: 180d          # Failed job retention (longer for debugging)
    workflow: 90d         # Workflow job retention
    script: 90d           # Script job retention
  logs:
    default: 30d          # Default log retention (shorter than jobs)
    error: 90d            # Error logs retained longer for debugging
    llm: 30d              # LLM call logs
    api: 30d              # API call logs
  audit_logs:
    default: 365d         # Default audit log retention (1 year)
    auth: 730d            # Auth-related logs (2 years for compliance)
    admin: 730d           # Admin action logs (2 years)
    read: 90d             # Read operations (lower priority)
  metrics:
    performance: 365d     # Performance metrics retention (Prometheus)
  files:
    global: indefinite    # Global files never auto-deleted
    workflow: job+7d      # Workflow files deleted 7 days after job retention
  cleanup:
    interval: 1h          # Cleanup job interval
    batch_size: 1000      # Records per cleanup batch
    logs_interval: 6h # Logs cleanup interval (more frequent)
    logs_batch_size: 5000 # Job log records per cleanup batch
    audit_interval: 24h   # Audit log cleanup interval
    audit_batch_size: 10000 # Audit records per cleanup batch
    enabled: true         # Enable/disable automatic cleanup
```

#### Cleanup Components

**1. Event Cleanup:**
- One-time events deleted after job completion (success or max retries exhausted)
- Recurring events deleted when recurrence expires (no more schedules to generate)
- Inactive events optionally deleted after configurable period
- Event deletion triggers cascade cleanup of associated schedules

**2. Schedule Cleanup (Redis):**
- Expired schedules automatically removed by Redis TTL
- Orphaned schedules (event deleted) cleaned up periodically
- Failed schedule execution retries tracked and cleaned

**3. Job Cleanup:**
- Jobs cleaned up based on retention policy
- Hierarchical cleanup: parent job deletion cascades to child jobs
- Failed jobs retained longer for debugging
- Configurable per-job-type retention periods

**4. Logs Cleanup:**
- Runs every 6 hours (more frequent than other cleanup)
- Logs cleaned based on level-specific retention
- Error logs retained longer (90 days) for debugging
- Logs deleted when parent job is deleted (CASCADE)
- Independent cleanup for orphaned logs
- High batch size (5,000) for efficiency

**5. File Cleanup:**
- Job files (`job/`) deleted immediately after job completion
- Workflow files (`workflow/`) deleted based on workflow retention
- Event files (`event/`) deleted when event is deleted
- Global files (`global/`) managed manually or via API
- Orphaned files (no parent reference) cleaned periodically

**6. Audit Log Cleanup:**
- Runs daily (separate from main cleanup to avoid interference)
- Audit logs cleaned based on category-specific retention policies
- Auth and admin logs retained longer (730 days) for compliance
- Read operations cleaned earlier (90 days) due to high volume
- Optional archival to S3/GCS before deletion
- Cleanup operations themselves are logged to audit trail

#### Cleanup Scheduler

**Background Cleanup Job:**
```
Cleanup Scheduler
    ├── Runs every: configurable (default: 1 hour)
    ├── Batch size: configurable (default: 1000 records)
    └── Components:
        ├── EventCleanup
        │   ├── Delete completed one-time events
        │   ├── Delete expired recurring events
        │   └── Delete inactive events (optional)
        │
        ├── ScheduleCleanup
        │   ├── Remove orphaned schedules from Redis
        │   └── Clean failed schedule retries
        │
        ├── JobCleanup
        │   ├── Delete jobs past retention period
        │   ├── Delete failed jobs past extended retention
        │   └── Cascade delete child jobs
        │
        └── FileCleanup
            ├── Delete orphaned files
            ├── Delete expired workflow files
            └── Clean up temporary files
```

#### Retention API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /admin/retention | Get current retention policies |
| PUT | /admin/retention | Update retention policies |
| POST | /admin/cleanup/run | Trigger manual cleanup run |
| GET | /admin/cleanup/status | Get cleanup job status and stats |
| GET | /admin/cleanup/history | Get cleanup history |
| DELETE | /admin/jobs/expired | Force delete all expired jobs |
| DELETE | /admin/files/orphaned | Force delete orphaned files |

**Retention Policy Response:**
```json
{
  "policies": {
    "jobs": {
      "default": "90d",
      "failed": "180d",
      "workflow": "90d",
      "script": "90d"
    },
    "metrics": {
      "performance": "365d"
    },
    "files": {
      "global": "indefinite",
      "workflow": "job+7d"
    }
  },
  "cleanup": {
    "interval": "1h",
    "batch_size": 1000,
    "enabled": true,
    "last_run": "2024-01-01T00:00:00Z",
    "next_run": "2024-01-01T01:00:00Z"
  }
}
```

**Cleanup Status Response:**
```json
{
  "status": "idle",
  "last_run": {
    "started_at": "2024-01-01T00:00:00Z",
    "completed_at": "2024-01-01T00:05:30Z",
    "duration_ms": 330000,
    "stats": {
      "events_deleted": 50,
      "schedules_deleted": 120,
      "jobs_deleted": 5000,
      "logs_deleted": 15000,
      "audit_logs_deleted": 5000,
      "files_deleted": 200,
      "bytes_freed": 1073741824
    }
  },
  "next_run": "2024-01-01T01:00:00Z"
}
```

#### Cleanup Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qhronos_cleanup_runs_total` | Counter | `component` | Cleanup runs by component |
| `qhronos_cleanup_duration_seconds` | Histogram | `component` | Cleanup duration |
| `qhronos_cleanup_records_deleted_total` | Counter | `type` | Records deleted by type |
| `qhronos_cleanup_bytes_freed_total` | Counter | `type` | Storage freed by type |
| `qhronos_cleanup_errors_total` | Counter | `component` | Cleanup errors |
| `qhronos_retention_oldest_job_age_seconds` | Gauge | `type` | Age of oldest job by type |
| `qhronos_storage_usage_bytes` | Gauge | `scope` | Storage usage by scope |

#### Data Archival (Optional)

For compliance requirements, optional archival before deletion:

**Archive Configuration:**
```yaml
archival:
  enabled: false           # Enable archival before deletion
  destination: "s3"        # Archive destination (s3, gcs, local)
  bucket: "qhronos-archive"
  path_prefix: "archive/"
  format: "jsonl"          # Archive format (jsonl, parquet)
  compress: true           # Compress archived data
  encrypt: true            # Encrypt archived data
  retention: "7y"          # Archive retention (compliance)
```

**Archive Process:**
1. Before deletion, records are exported to archive storage
2. Archives are organized by date and type
3. Archives can be queried for compliance/audit purposes
4. Archives are pruned based on archive retention policy

#### Cleanup Best Practices

1. **Gradual Deletion**: Delete in batches to avoid database locks
2. **Off-Peak Scheduling**: Run cleanup during low-traffic periods
3. **Monitoring**: Alert on cleanup failures or unusually high deletion rates
4. **Dry Run**: Support dry-run mode for testing retention changes
5. **Audit Trail**: Log all deletion operations for compliance
6. **Graceful Degradation**: Continue processing if cleanup fails

---

## 5. Architecture Deep Dive

### 5.1 API Layer
- Built with Gin (Go web framework)
- Exposes RESTful endpoints for all core resources
- Applies global and route-specific middleware
- WebSocket support for real-time delivery

### 5.2 Handlers
- Implement HTTP request handling for events, jobs, tokens, workflows, scripts
- Validate input, invoke business logic, and format responses
- Support for JSON request/response bodies

### 5.3 Middleware
- Cross-cutting concerns: logging, error handling, authentication, rate limiting
- Ensures consistent request/response processing and security
- **Ginzap Logger:** Uses `zap` for structured logging of HTTP requests and responses
- **RequestIDMiddleware:** Injects unique request ID for traceability

### 5.4 Services
- Encapsulate business logic not directly tied to HTTP or data access
- Examples: token management, HMAC signing, scheduling logic, workflow orchestration

### 5.5 Repository Layer
- Data access layer using sqlx for PostgreSQL
- Implements CRUD operations for events, jobs, workflows, scripts
- Maps Go models to database tables

### 5.6 Scheduler Layer
- Background jobs for event expansion, webhook dispatch, and cleanup
- Uses Redis for coordination and scheduling of tasks
- **Core Scheduler (`scheduler.Scheduler`):** Manages scheduling mechanism in Redis
- **Expander (`scheduler.Expander`):** Generates jobs for recurring events
- **Dispatcher (`scheduler.Dispatcher`):** Delivers events via action system
- **Cleanup (`scheduler.Cleanup`):** Deletes completed events, removes expired schedules, retains jobs

### 5.7 Action System
- Extensible action execution framework
- **ActionsManager**: Coordinates action execution
- Action types: webhook, websocket, apicall, script, llm, workflow
- Timeout handling and retry logic
- Error handling and failure reporting
- Execution logging for all attempts

### 5.8 Workflow Engine
- Orchestrates multi-step workflow execution
- Manages workflow job lifecycle (jobs with action_type='workflow')
- Coordinates step execution and state transitions
- Handles conditional branching and loops
- Manages workflow variables and data flow
- Creates jobs for workflow, steps, and actions

### 5.9 Script Runtime
- Goja JavaScript runtime for script execution
- Sandboxed execution environment
- Module system with require() support
- Context injection (input, steps, workflow, console)
- Timeout enforcement
- Creates action jobs (type: script) after execution

### 5.10 Object Storage Integration
- MinIO/S3 compatible storage backend
- Global file storage for shared resources
- Workflow-scoped file storage for instance data
- File operations API for scripts

### 5.11 Logging System
- Persistent logging of all job executions
- **Unified Log Structure**: Single log table with type-specific fields
- **Hierarchical Logging**: Job → Workflow → Step → Action log hierarchy
- **Type-Specific Fields**: Each log type has its own additional fields
- Queryable via `/jobs` API endpoint for auditing and debugging
- Job details accessible via `/jobs/:id` endpoint

### 5.12 Models
- Defines data structures for events, jobs, tokens, workflows, scripts, errors
- Used throughout handlers, services, and repositories

### 5.13 Database
- PostgreSQL is the source of truth for all persistent data
- Schema includes tables for events, jobs, workflows, scripts
- Indexes and triggers support performance and data integrity
- Jobs table is append-only

### 5.14 Configuration
- Loads settings from YAML files and environment variables
- Centralizes configuration for database, Redis, authentication, scheduler, object storage

---

## 6. Business Logic Flows

### 6.1 Event Lifecycle
- **Create:** Client sends POST request to `/events` with event details. Handler validates input and stores event in database. If recurring, marked for expansion.
- **Update:** Client sends PUT request to `/events/{id}`. Handler validates and updates event. Changes to recurrence reflected in future schedules.
- **Delete:** Client sends DELETE request to `/events/{id}`. Event, future schedules, and associated jobs removed immediately.
- **Automatic Cleanup:** 
  - One-time events: Deleted after job completes (success or failure after max retries)
  - Recurring events: Deleted when recurrence expires (no more schedules to generate)
  - Jobs retained for all completed events (serve as audit trail)

### 6.2 Recurring Event Expansion
- Expander job periodically scans for recurring events needing new schedules
- Computes next set of schedules based on lookahead window
- Creates schedules in Redis with execution time
- Checks if recurrence has expired and deletes event if so

### 6.3 Schedule Execution
- Dispatcher finds due schedules in Redis (time <= now)
- Creates a job in PostgreSQL with status `pending`
- Removes schedule from Redis
- Job status transitions: `pending` → `running` → `completed`/`failed`
- Jobs are never deleted, serve as audit trail

### 6.4 Webhook Dispatch & Retry
- Dispatcher finds due schedules in Redis
- Creates job (type: `job`) in PostgreSQL with status `pending`
- Removes schedule from Redis
- Updates job status to `running`
- Attempts to deliver via action system (webhook, websocket, apicall, etc.)
- Signs with HMAC if configured
- Creates action job (type: `webhook`, `apicall`, etc.) linked to parent job
- On success, updates job status to `completed`
- On failure, updates job status to `failed` and retries with backoff (creates new schedule if retry needed)
- Jobs retained indefinitely

### 6.5 Workflow Execution Flow
- Workflow execution can be:
  - Direct: Client calls `POST /workflows/{id}/execute` with params
  - Scheduled: Creates a schedule in Redis, which later creates a job when due
- **Execution Request:**
  - Accepts `params` JSON object (optional)
  - Params are passed as workflow input and accessible via `input` in templates/conditions/scripts
- Creates a job (type: `job`) immediately in PostgreSQL with status `pending`
- Job `data` field contains: `workflow_id`, `input` (from params), `output`, `variables`
- Workflow dispatcher picks up job
- Creates workflow job (type: `workflow`) linked to parent job
- Steps executed according to definition:
  - Resolve variables/templates (can reference `input` params)
  - Execute step based on type
  - For action steps:
    - Execute action (script, api_call, webhook, etc.)
    - Create action job (type: `script`, `api_call`, etc.) after action executes
    - Create step job (type: `step`) after action job, referencing the action job
  - For other step types:
    - Create step job (type: `step`) after step execution
  - Link step job to workflow job via `parent_job_id`
  - Handle timeouts and errors
  - Update job state (workflow state stored in job `data` field)
  - Determine next step(s)
- Job status updated to `completed` or `failed`
- All jobs retained (job, workflow, steps, actions)

### 6.6 Script Execution Flow

**Direct Script Execution:**
- Client calls `POST /scripts/{id}/execute` with params
- **Execution Request:**
  - Accepts `params` JSON object (optional)
  - Params are passed as script input and accessible via `input` in script
- Creates a job (type: `job`) immediately in PostgreSQL with status `pending`
- Job `data` field contains: `script_id`, `script_version`, `input` (from params), `output`, `variables` (if set)
- Script loaded from repository
- Execution context prepared (input from params, steps={}, workflow={}, console)
- Script executed in Goja runtime with timeout
- Job status updated to `running`, then `completed` or `failed`
- Action job created (type: `script`) with input, output, duration, errors
- Variables extracted from script output (if `_variables` key present)
- Return value stored in job `data.output`
- Errors caught and job status set to `failed`
- All jobs retained

**Script Execution within Workflow:**
- Script loaded from repository
- Execution context prepared (input from step, steps, workflow, console)
- Script executed in Goja runtime with timeout
- Action job created (type: `script`) with input, output, duration, errors
- Variables extracted from script output (if `_variables` key present)
- Return value becomes step output
- Errors caught and job status set to `failed`
- Step job created after script job
- All jobs retained

### 6.7 Token Management
- Admins create JWT tokens via `/tokens` endpoint
- Tokens encode access level and scope
- Tokens validated on each API request
- Scope-based filtering applied

### 6.8 Rate Limiting
- Each request checked against Redis-backed token bucket rate limiter
- Exceeding limit results in 429 response
- Rate limits configurable per token

### 6.9 Cleanup & Retention
- Cleanup job periodically scans for completed events
- Deletes one-time events after job completion
- Deletes recurring events when recurrence expires
- Deletes completed jobs (success or failure after max retries)
- Retains all logs indefinitely

---

## 7. Data Model

### 7.1 Internal/System Jobs

Internal/system jobs use the same event, schedule, and job management infrastructure but are marked as private and only accessible with admin privileges.

**System Job Characteristics:**
- Marked with `is_system=true` flag
- `project_id` is NULL (not scoped to any project)
- Created by system components (cleanup, retention, health checks, etc.)
- Only visible via API when using admin token (role='admin')
- Use same job types and execution flow as regular jobs
- Subject to same retention policies

**Use Cases:**
- Cleanup job executions
- Retention policy enforcement jobs
- System health check jobs
- Maintenance tasks
- Background processing

**API Access Control:**
- Regular tokens (read/write): Cannot see system jobs/events
- Admin tokens: Can see all jobs/events including system ones
- System jobs filtered out by default in repository queries unless admin token is used

**Example System Job:**
```json
{
  "id": "job-system-cleanup-123",
  "project_id": null,
  "is_system": true,
  "type": "job",
  "status": "completed",
  "data": {
    "event_id": null,
    "action_type": "cleanup",
    "description": "Scheduled cleanup job"
  }
}
```

### 7.2 Core Entities

**Events:**
- Event definitions with metadata, schedule, and action configuration
- Support for one-time and recurring events
- Tag-based organization
- Status tracking (active, inactive)
- **System Events**: Internal/system events marked with `is_system=true`, only visible to admin tokens
- Deleted when done (recurrence expired or one-time completed)

**Schedules:**
- Temporary scheduled executions stored in Redis
- Created by the Expander for recurring events
- Contains: event_id, execution_time, action_config
- Removed from Redis when executed or expired
- Not persisted to PostgreSQL

**Jobs:**
- Persistent execution records stored in PostgreSQL
- Created when schedules are executed or workflows are triggered directly
- **General Fields**: id, schedule_id (if from schedule), type, status, started_at, completed_at, duration_ms, error_message, parent_job_id, is_system
- **Type-Specific Fields**: Stored in JSONB `data` field
- **Job Types**: job, workflow, step, api_call, script, webhook, websocket, llm
- **Job Hierarchy**: Job → Workflow → Step → Action jobs (via `parent_job_id`)
- **Status**: pending, running, completed, failed, cancelled
- **System Jobs**: Internal/system jobs marked with `is_system=true`, only visible to admin tokens
- Never deleted, serve as audit trail

**Job Structure Details:**

**General Job Fields (all types):**
- `id`: UUID, unique job identifier
- `project_id`: UUID, reference to project (null for system jobs)
- `schedule_id`: UUID, reference to schedule that created this job (null if direct execution)
- `type`: enum (job, workflow, step, api_call, script, webhook, websocket, llm)
- `status`: enum (pending, running, completed, failed, cancelled)
- `is_system`: boolean, true for internal/system jobs (default: false)
- `started_at`: timestamp, when execution started
- `completed_at`: timestamp, when execution completed (null if still running)
- `duration_ms`: integer, execution duration in milliseconds
- `error_message`: text, error message if execution failed
- `parent_job_id`: UUID, reference to parent job (null for top-level jobs)
- `data`: JSONB, type-specific fields

**Type-Specific Fields (stored in `data` JSONB):**

- **job**: `event_id` (if from event), `workflow_id` (if workflow execution), `script_id` (if script execution), `action_type`, `attempt_number`, `input` (from params), `output`, `variables`
- **workflow**: `workflow_id`, `input` (from execution params), `output`, `variables`
- **step**: `step_id`, `step_name`, `step_type`, `input`, `output`, `action_job_id` (if action step)
- **api_call**: `url`, `method`, `headers`, `request_body`, `response_status`, `response_body`, `timeout_ms`
- **script**: `script_id`, `script_version`, `input` (from params or step input), `output`, `variables` (if set)
- **webhook**: `url`, `headers`, `payload`, `response_status`, `response_body`, `hmac_signature`
- **websocket**: `connection_id`, `message`, `response`
- **integration**: `integration_id`, `integration_type`, `provider`, `input`, `output`, `metadata`
  - For LLM: `model`, `prompt`, `response`, `tokens_used`, `cost`
  - For notification channels: `channel`, `recipient`, `subject` (email), `body`, `status`

**Logs:**
- Lightweight execution logs for detailed debugging (console output, LLM I/O, API responses)
- Stored separately from jobs table for performance
- Cleaned up based on retention policy (shorter than jobs)

### 7.3 Logs

Logs provide detailed execution traces without bloating the jobs table.

**Logs Table Schema:**
```sql
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    level VARCHAR(20) NOT NULL CHECK (level IN ('debug', 'info', 'warn', 'error')),
    category VARCHAR(50) NOT NULL,  -- 'console', 'llm', 'api', 'db', 'http', 'notification', 'file'
    message TEXT,
    data JSONB,  -- Category-specific structured data
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX idx_logs_job_id ON logs(job_id);
CREATE INDEX idx_logs_project_id ON logs(project_id);
CREATE INDEX idx_logs_timestamp ON logs(timestamp DESC);
CREATE INDEX idx_logs_category ON logs(category);
CREATE INDEX idx_logs_level ON logs(level);

-- Composite index for common query pattern
CREATE INDEX idx_logs_job_timestamp ON logs(job_id, timestamp DESC);
```

**Log Categories & Data Schemas:**

| Category | Description | Data Fields |
|----------|-------------|-------------|
| `console` | Script console.log/warn/error | `args` (array of logged values) |
| `llm` | LLM API calls | `provider`, `model`, `prompt`, `response`, `tokens`, `cost`, `duration_ms` |
| `api` | HTTP API calls | `method`, `url`, `request_headers`, `request_body`, `response_status`, `response_body`, `duration_ms` |
| `db` | Database queries | `integration_id`, `operation`, `sql`, `params`, `rows_affected`, `duration_ms` |
| `http` | Webhook/API call actions | `url`, `method`, `status`, `duration_ms` |
| `notification` | Notification sends | `channel`, `recipient`, `status`, `provider_response` |
| `file` | File operations | `operation`, `path`, `size`, `duration_ms` |
| `spreadsheet` | Spreadsheet operations | `integration_id`, `operation`, `range`, `rows`, `duration_ms` |

**Log Entry Examples:**

```json
// Console log (script)
{
  "id": "log-123",
  "job_id": "job-456",
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "info",
  "category": "console",
  "message": "Processing user data",
  "data": {
    "args": ["Processing user data", { "userId": 123 }]
  }
}

// LLM call
{
  "id": "log-124",
  "job_id": "job-456",
  "timestamp": "2024-01-15T10:30:01.456Z",
  "level": "info",
  "category": "llm",
  "message": "OpenAI GPT-4 call completed",
  "data": {
    "provider": "openai",
    "model": "gpt-4",
    "prompt": "Summarize: ...",
    "response": "Summary: ...",
    "tokens": { "prompt": 150, "completion": 50, "total": 200 },
    "cost": 0.0045,
    "duration_ms": 1234
  }
}

// API call
{
  "id": "log-125",
  "job_id": "job-456",
  "timestamp": "2024-01-15T10:30:02.789Z",
  "level": "info",
  "category": "api",
  "message": "POST https://api.example.com/users -> 201",
  "data": {
    "method": "POST",
    "url": "https://api.example.com/users",
    "request_headers": { "Content-Type": "application/json" },
    "request_body": { "name": "John" },
    "response_status": 201,
    "response_body": { "id": 123, "name": "John" },
    "duration_ms": 234
  }
}

// Database query
{
  "id": "log-126",
  "job_id": "job-456",
  "timestamp": "2024-01-15T10:30:03.012Z",
  "level": "info",
  "category": "db",
  "message": "SELECT query returned 5 rows",
  "data": {
    "integration_id": "int-789",
    "operation": "query",
    "sql": "SELECT * FROM users WHERE active = $1",
    "params": [true],
    "rows_affected": 5,
    "duration_ms": 12
  }
}

// Error log
{
  "id": "log-127",
  "job_id": "job-456",
  "timestamp": "2024-01-15T10:30:04.345Z",
  "level": "error",
  "category": "api",
  "message": "API call failed: connection timeout",
  "data": {
    "method": "GET",
    "url": "https://api.slow.com/data",
    "error": "connection timeout after 30s",
    "duration_ms": 30000
  }
}
```

**Performance Considerations:**

1. **Async Batch Insert:**
   - Logs are buffered in memory (channel buffer: 10,000)
   - Background worker batch-inserts every 100ms or 100 logs
   - Non-blocking: log writes don't slow down job execution

2. **Data Size Limits:**
   - `message`: Max 1KB
   - `data` JSONB: Max 64KB per log entry
   - Large payloads (responses > 64KB) are truncated with `[truncated]` marker
   - Option to store large payloads in object storage with reference

3. **Log Level Filtering:**
   - Configurable minimum log level per project
   - Default: `info` (skips `debug` in production)

4. **Sampling for High-Volume:**
   ```yaml
   logs:
     buffer_size: 10000
     batch_size: 100
     flush_interval: 100ms
     max_message_size: 1024      # 1KB
     max_data_size: 65536        # 64KB
     min_level: info             # debug, info, warn, error
     sampling:
       enabled: false
       rate: 1.0                 # Log 100% by default
       categories:
         console: 0.1            # Sample 10% of console logs in high-volume
   ```

**Workflows:**
- Workflow definitions with step configurations
- Versioning support
- Status tracking (active, inactive)
- Tag-based organization


**Scripts:**
- JavaScript code storage
- Versioning support
- Status tracking (active, inactive)
- Tag-based organization

### 7.2 Relationships

```
[events] <1-----n> [schedules] (Redis, temporary)
   |                        |
   |                        +----< (removed when executed)
   +----< (deleted when done)

[schedules] ──► [jobs] (PostgreSQL, permanent)
   (when executed)

[workflows] <1-----n> [jobs] (via type='workflow')
   |                        |
   |                        +----< (never deleted)
   |
   +----< scripts (via script actions)

[integrations] <1-----n> [jobs] (via integration actions)
   |                        |
   |                        +----< (never deleted)
   |
   ├── LLM integrations (openai, anthropic, gemini, openrouter)
   └── Notification integrations (ses, twilio, slack, discord, telegram)

[jobs] (unified table in PostgreSQL)
   ├── job jobs (type: job, top-level)
   ├── workflow jobs (type: workflow, parent: job)
   ├── step jobs (type: step, parent: workflow job)
   └── action jobs (type: script|api_call|webhook|integration|etc., parent: step job or job)

[performance_metrics] (Prometheus aggregates)
```

### 7.3 Jobs Database Schema

**Unified Jobs Table (`jobs`):**

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id), -- NULL for system jobs
    schedule_id UUID, -- Reference to schedule that created this job (null if direct execution)
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

CREATE INDEX idx_jobs_schedule_id ON jobs(schedule_id);
CREATE INDEX idx_jobs_type ON jobs(type);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_is_system ON jobs(is_system);
CREATE INDEX idx_jobs_project_id ON jobs(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX idx_jobs_started_at ON jobs(started_at);
CREATE INDEX idx_jobs_parent_job_id ON jobs(parent_job_id);
CREATE INDEX idx_jobs_data_gin ON jobs USING GIN(data);
```

**Schedules (Redis):**
- Stored as Redis keys with TTL
- Key format: `schedule:{id}`
- Value: JSON containing event_id, execution_time, action_config
- Sorted sets used for efficient querying by execution time

**Integrations Table (`integrations`):**

```sql
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('llm', 'notification', 'database', 'spreadsheet')),
    provider VARCHAR(100) NOT NULL,
    config JSONB NOT NULL, -- Encrypted credentials and provider-specific config
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_integrations_type ON integrations(type);
CREATE INDEX idx_integrations_provider ON integrations(provider);
CREATE INDEX idx_integrations_status ON integrations(status);
CREATE INDEX idx_integrations_tags ON integrations USING GIN(tags);
```

**Integration Configuration Examples:**

**LLM Integration Config:**
```json
{
  "api_key": "encrypted-api-key",
  "default_model": "gpt-4",
  "default_temperature": 0.7,
  "default_max_tokens": 2000,
  "base_url": "https://api.openai.com/v1"
}
```

**Amazon SES Integration Config:**
```json
{
  "region": "us-east-1",
  "access_key_id": "encrypted-access-key",
  "secret_access_key": "encrypted-secret-key",
  "default_from_email": "noreply@example.com",
  "default_from_name": "Qhronos"
}
```

**Twilio Integration Config:**
```json
{
  "account_sid": "encrypted-account-sid",
  "auth_token": "encrypted-auth-token",
  "default_from_number": "+1234567890"
}
```

**MySQL Integration Config:**
```json
{
  "host": "localhost",
  "port": 3306,
  "database": "mydb",
  "username": "encrypted-username",
  "password": "encrypted-password",
  "max_connections": 10,
  "connection_timeout_ms": 5000
}
```

**PostgreSQL Integration Config:**
```json
{
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "username": "encrypted-username",
  "password": "encrypted-password",
  "sslmode": "require",
  "max_connections": 10,
  "connection_timeout_ms": 5000
}
```

**Google Sheets Integration Config:**
```json
{
  "credentials": "encrypted-service-account-json",
  "default_spreadsheet_id": "optional-default-spreadsheet-id"
}
```

**Job Type-Specific Fields (stored in `data` JSONB):**

- **job**: `event_id`, `action_type`, `attempt_number`, `input`, `output`
- **workflow**: `workflow_id`, `input`, `output`, `variables`
- **step**: `step_id`, `step_name`, `step_type`, `input`, `output`, `action_job_id` (if action step)
- **api_call**: `url`, `method`, `headers`, `request_body`, `response_status`, `response_body`, `timeout_ms`
- **script**: `script_id`, `script_version`, `input`, `output`, `variables` (if set), `console_output`
- **webhook**: `url`, `headers`, `payload`, `response_status`, `response_body`, `hmac_signature`
- **websocket**: `connection_id`, `message`, `response`
- **integration**: `integration_id`, `integration_type`, `provider`, `input`, `output`, `metadata`
  - For LLM: `model`, `prompt`, `response`, `tokens_used`, `cost`
  - For notification channels: `channel`, `recipient`, `subject` (email), `body`, `status`
  - For database: `query`, `params`, `rows_affected`, `result`

---

## 8. API Reference

### 8.1 Event Endpoints

| Method | Path                  | Description                        |
|--------|-----------------------|------------------------------------|
| POST   | /events               | Create a new event                 |
| GET    | /events/{id}          | Get event by ID                    |
| PUT    | /events/{id}          | Update event by ID                 |
| DELETE | /events/{id}          | Delete event by ID                 |
| GET    | /events               | List events (filterable by tags)   |

### 8.2 Job Endpoints

| Method | Path                  | Description                        |
|--------|-----------------------|------------------------------------|
| GET    | /jobs/{id}            | Get job by ID (system jobs only visible to admin) |
| GET    | /jobs                 | List jobs (filterable, system jobs filtered unless admin) |
| GET    | /events/{id}/jobs     | List jobs for event (system jobs filtered unless admin) |
| GET    | /jobs/{id}/logs       | Get execution logs for job (system job logs only visible to admin) |

**System Job Access:**
- System jobs (`is_system=true`) are automatically filtered out for non-admin tokens
- Admin tokens (role='admin') can access all jobs including system jobs
- System jobs can be explicitly included by adding `?include_system=true` (admin only)

### 8.3 Job Endpoints (continued)

| Method | Path                  | Description                        |
|--------|-----------------------|------------------------------------|
| GET    | /jobs/{id}/children   | List child jobs for a job (includes all child jobs) |
| GET    | /workflows/{id}/jobs   | List jobs for workflow executions |
| GET    | /scripts/{id}/jobs    | List jobs for script executions |
| GET    | /schedules            | List schedules in Redis (for monitoring) |

### 8.3.1 Logs Endpoint

**Get Logs:**
```
GET /jobs/{id}/logs?level=info&category=llm&limit=100&cursor=xxx
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | string | all | Filter by log level (debug, info, warn, error) |
| `category` | string | all | Filter by category (console, llm, api, db, http, notification, file, spreadsheet) |
| `limit` | int | 100 | Max logs to return (max 1000) |
| `cursor` | string | - | Pagination cursor (log ID for next page) |
| `order` | string | desc | Sort order (asc, desc by timestamp) |

**Response:**
```json
{
  "data": [
    {
      "id": "log-123",
      "job_id": "job-456",
      "timestamp": "2024-01-15T10:30:00.123Z",
      "level": "info",
      "category": "console",
      "message": "Processing user data",
      "data": {
        "args": ["Processing user data", { "userId": 123 }]
      }
    },
    {
      "id": "log-124",
      "job_id": "job-456",
      "timestamp": "2024-01-15T10:30:01.456Z",
      "level": "info",
      "category": "llm",
      "message": "OpenAI GPT-4 call completed",
      "data": {
        "provider": "openai",
        "model": "gpt-4",
        "tokens": { "prompt": 150, "completion": 50, "total": 200 },
        "cost": 0.0045,
        "duration_ms": 1234
      }
    }
  ],
  "pagination": {
    "cursor": "log-124",
    "has_more": true,
    "total": 45
  }
}
```

**Get Logs for Child Jobs (recursive):**
```
GET /jobs/{id}/logs?include_children=true
```

This returns logs from the job and all its child jobs (workflow steps, action executions), ordered by timestamp.

### 8.4 Workflow Endpoints

| Method | Path                  | Description                        |
|--------|-----------------------|------------------------------------|
| POST   | /workflows            | Create a new workflow              |
| GET    | /workflows/{id}       | Get workflow by ID                 |
| PUT    | /workflows/{id}       | Update workflow by ID              |
| DELETE | /workflows/{id}       | Delete workflow by ID              |
| GET    | /workflows            | List workflows                     |
| POST   | /workflows/{id}/execute | Execute workflow with params (creates a job) |
| GET    | /workflows/{id}/jobs    | List jobs for workflow (workflow executions) |

**Workflow Execution Request:**
```json
POST /workflows/{id}/execute
{
  "params": {
    "key1": "value1",
    "key2": 123,
    "key3": { "nested": "object" }
  }
}
```

**Workflow Execution Response:**
```json
{
  "id": "job-uuid",
  "type": "job",
  "status": "pending",
  "data": {
    "workflow_id": "workflow-uuid",
    "input": { "key1": "value1", "key2": 123, "key3": { "nested": "object" } }
  },
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 8.5 Script Endpoints

| Method | Path                  | Description                        |
|--------|-----------------------|------------------------------------|
| POST   | /scripts              | Create a new script                |
| GET    | /scripts/{id}         | Get script by ID                   |
| PUT    | /scripts/{id}         | Update script (creates new version)|
| DELETE | /scripts/{id}         | Delete script                      |
| GET    | /scripts              | List scripts                       |
| POST   | /scripts/{id}/execute | Execute script with params (creates a job) |
| GET    | /scripts/{id}/jobs    | List jobs for script executions |

### 8.6 Integration Endpoints

| Method | Path                  | Description                        |
|--------|-----------------------|------------------------------------|
| POST   | /integrations         | Create a new integration           |
| GET    | /integrations/{id}    | Get integration by ID              |
| PUT    | /integrations/{id}    | Update integration                 |
| DELETE | /integrations/{id}    | Delete integration                 |
| GET    | /integrations         | List integrations (filterable by type) |
| GET    | /integrations/{id}/jobs | List jobs for integration executions |

**Integration Types:**
- `llm`: LLM provider integrations (openai, anthropic, gemini, openrouter)
- `notification`: Notification channel integrations (ses, twilio, slack, discord, telegram)
- `database`: Database integrations (mysql, postgres)
- `spreadsheet`: Spreadsheet integrations (google_sheets)

**Create LLM Integration Request:**
```json
POST /integrations
{
  "name": "OpenAI Production",
  "type": "llm",
  "provider": "openai",
  "config": {
    "api_key": "sk-...",
    "default_model": "gpt-4",
    "default_temperature": 0.7,
    "default_max_tokens": 2000
  }
}
```

**Create Notification Integration Request:**
```json
POST /integrations
{
  "name": "Amazon SES Production",
  "type": "notification",
  "provider": "ses",
  "config": {
    "region": "us-east-1",
    "access_key_id": "AKIA...",
    "secret_access_key": "...",
    "default_from_email": "noreply@example.com"
  }
}
```

**Create Twilio Integration Request:**
```json
POST /integrations
{
  "name": "Twilio Production",
  "type": "notification",
  "provider": "twilio",
  "config": {
    "account_sid": "AC...",
    "auth_token": "...",
    "default_from_number": "+1234567890"
  }
}
```

**Integration Action Example:**
```json
{
  "type": "integration",
  "integration_id": "integration-uuid",
  "params": {
    "prompt": "Generate a summary",
    "model": "gpt-4"
  }
}
```

**Notification Action Example:**
```json
{
  "type": "integration",
  "integration_id": "ses-integration-uuid",
  "params": {
    "to": "user@example.com",
    "subject": "Notification",
    "body": "Your request has been processed"
  }
}
```

**Script Execution Request:**
```json
POST /scripts/{id}/execute
{
  "params": {
    "key1": "value1",
    "key2": 123,
    "key3": { "nested": "object" }
  }
}
```

**Script Execution Response:**
```json
{
  "id": "job-uuid",
  "type": "job",
  "status": "pending",
  "data": {
    "script_id": "script-uuid",
    "script_version": 1,
    "input": { "key1": "value1", "key2": 123, "key3": { "nested": "object" } }
  },
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 8.6 Token Endpoints

| Method | Path                  | Description                        |
|--------|-----------------------|------------------------------------|
| POST   | /tokens               | Create a new JWT token (admin)     |

### 8.8 System Endpoints

| Method | Path                  | Description                        |
|--------|-----------------------|------------------------------------|
| GET    | /status               | Service status and health info     |
| GET    | /health               | Simple health check (liveness)     |
| GET    | /ready                | Readiness check (dependencies)     |
| GET    | /metrics              | Prometheus metrics endpoint        |
| WS     | /ws                   | Real-time event delivery via WebSocket |

### 8.9 Admin Endpoints (Retention & Cleanup)

| Method | Path                    | Description                          |
|--------|-------------------------|--------------------------------------|
| GET    | /admin/retention        | Get current retention policies       |
| PUT    | /admin/retention        | Update retention policies            |
| POST   | /admin/cleanup/run      | Trigger manual cleanup run           |
| GET    | /admin/cleanup/status   | Get cleanup job status and stats     |
| GET    | /admin/cleanup/history  | Get cleanup run history              |
| DELETE | /admin/jobs/expired     | Force delete all expired jobs        |
| DELETE | /admin/files/orphaned   | Force delete orphaned files          |
| GET    | /admin/storage/usage    | Get storage usage by scope           |
| POST   | /admin/archive/export   | Export data to archive (if enabled)  |

**Note:** Admin endpoints require `admin` access level.

---

## 9. Security

### 9.1 Authentication
- **Master Token:** Static API key with full access
- **JWT Token:** Issued via `/tokens` endpoint (admin only). Encodes user, access level, and scope.

### 9.2 Authorization
- Access controlled by token type, access level (`read`, `write`, `admin`), and scope (tags)
- Master token bypasses all restrictions
- JWT tokens checked for required access and scope

### 9.3 Webhook HMAC Signing
- All webhook deliveries signed using HMAC-SHA256
- Signature included in `X-Qhronos-Signature` header
- Each event can specify custom secret or use system default
- Recipients should verify signature for authenticity

### 9.4 Script Security
- Sandboxed execution in isolated Goja runtime
- No file system access (only via `require('files')` module)
- No network access (only via `fetch` API)
- No process execution
- Timeout enforcement
- Resource limits (memory, CPU)
- Code validation before storage
- Access control via workflow system
- Versioning for rollback capability
- Audit logging via jobs

---

## 10. Operational Concerns

### 10.1 Deployment
- Designed for containerized deployment (Docker/Kubernetes)
- Requires PostgreSQL, Redis, and object storage (MinIO/S3) as dependencies
- Configuration managed via YAML files and environment variables
- Embedded migrations for database schema management

### 10.2 Monitoring & Observability
- Exposes `/status` and `/health` endpoints for liveness and readiness checks
- Exposes `/ready` endpoint for dependency health (database, Redis, storage)
- Structured logging suitable for aggregation (ELK, Loki)
- Jobs queryable via `/jobs` API endpoint for auditing and debugging
- Job details accessible via `/jobs/:id` endpoint
- Prometheus metrics export via `/metrics` endpoint

### 10.3 Horizontal Scalability

Qhronos is designed for horizontal scalability with stateless components and distributed coordination.

**Stateless Components:**

| Component | Scaling Strategy | Notes |
|-----------|------------------|-------|
| API Servers | Horizontal (replicas) | Load balanced, no session state |
| Expander Workers | Horizontal (replicas) | Distributed locking via Redis |
| Dispatcher Workers | Horizontal (replicas) | Work distribution via Redis queues |
| Workflow Workers | Horizontal (replicas) | Work distribution via Redis queues |
| Cleanup Workers | Single leader | Leader election via Redis |

**Multi-Instance Architecture:**

```
                    ┌─────────────────────────────────────────────┐
                    │              Load Balancer                   │
                    └─────────────────────────────────────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
              ▼                         ▼                         ▼
     ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
     │ API Server  │           │ API Server  │           │ API Server  │
     │  Instance 1 │           │  Instance 2 │           │  Instance N │
     └─────────────┘           └─────────────┘           └─────────────┘
              │                         │                         │
              └─────────────────────────┼─────────────────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
              ▼                         ▼                         ▼
     ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
     │   Expander  │           │  Dispatcher │           │  Workflow   │
     │   Workers   │           │   Workers   │           │   Workers   │
     └─────────────┘           └─────────────┘           └─────────────┘
              │                         │                         │
              └─────────────────────────┼─────────────────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
              ▼                         ▼                         ▼
     ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
     │  PostgreSQL │           │    Redis    │           │ Object      │
     │  (Primary/  │           │  (Cluster/  │           │ Storage     │
     │   Replica)  │           │   Sentinel) │           │ (S3/MinIO)  │
     └─────────────┘           └─────────────┘           └─────────────┘
```

**Distributed Work Distribution:**

1. **Schedule Processing:**
   - Expander workers use distributed locking (Redis SETNX) to prevent duplicate schedule creation
   - Each worker processes a subset of events using consistent hashing
   - Lock TTL ensures recovery if worker crashes

2. **Job Dispatching:**
   - Dispatcher workers pull from Redis sorted set (ZPOPMIN atomic operation)
   - Work stealing pattern for load balancing
   - At-least-once delivery with idempotency checks

3. **Workflow Execution:**
   - Workflow jobs queued in Redis lists (BRPOPLPUSH for reliability)
   - Worker claims job and updates status atomically
   - Heartbeat mechanism for stalled job detection

**Configuration for Multi-Instance:**
```yaml
scaling:
  instance_id: "${HOSTNAME}"  # Unique instance identifier
  
  expander:
    enabled: true
    workers: 4                # Workers per instance
    lock_ttl: 30s            # Distributed lock TTL
    batch_size: 100          # Events per batch
    
  dispatcher:
    enabled: true
    workers: 8               # Workers per instance
    poll_interval: 100ms     # Redis poll interval
    batch_size: 50           # Jobs per batch
    
  workflow:
    enabled: true
    workers: 4               # Workers per instance
    poll_interval: 100ms
    
  cleanup:
    enabled: true
    leader_election: true    # Only one instance runs cleanup
    leader_ttl: 60s
```

### 10.4 Resilience & Fault Tolerance

**Graceful Shutdown:**
- API servers drain connections before shutdown
- Background workers complete in-progress jobs
- Configurable shutdown timeout (default: 30s)
- SIGTERM/SIGINT signal handling

**Circuit Breaker Pattern:**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Closed    │────►│    Open     │────►│  Half-Open  │
│ (Normal)    │     │ (Failing)   │     │ (Testing)   │
└─────────────┘     └─────────────┘     └─────────────┘
       ▲                                       │
       └───────────────────────────────────────┘
```

| Component | Circuit Breaker | Recovery |
|-----------|-----------------|----------|
| Database | Yes | 5 failures → open, 30s recovery |
| Redis | Yes | 3 failures → open, 10s recovery |
| Webhooks | Per-URL | 5 failures → open, 60s recovery |
| Integrations | Per-provider | 3 failures → open, 30s recovery |
| Object Storage | Yes | 3 failures → open, 15s recovery |

**Retry Strategies:**

| Operation | Strategy | Max Retries | Backoff |
|-----------|----------|-------------|---------|
| Webhook delivery | Exponential | 5 | 1s, 2s, 4s, 8s, 16s |
| Integration calls | Exponential | 3 | 1s, 2s, 4s |
| Database queries | Linear | 3 | 100ms |
| Redis commands | Linear | 3 | 50ms |
| Workflow steps | Configurable | Per-step | Per-step |

**Job Recovery:**

1. **Stalled Job Detection:**
   - Jobs in `running` status with no heartbeat for >5 minutes
   - Automatic retry or failure based on configuration
   - Alert triggered for investigation

2. **Orphaned Schedule Recovery:**
   - Schedules in Redis with no corresponding event
   - Cleaned up during cleanup cycle
   - Logged for debugging

3. **Failed Job Handling:**
   - Configurable retry policy per action type
   - Dead letter queue for permanently failed jobs
   - Alert on repeated failures

**Health Checks:**

```yaml
health:
  # Liveness probe - is the process alive?
  liveness:
    path: /health
    interval: 10s
    timeout: 5s
    
  # Readiness probe - can it serve traffic?
  readiness:
    path: /ready
    interval: 5s
    timeout: 3s
    checks:
      - database
      - redis
      - object_storage
```

**Dependency Health Monitoring:**

| Dependency | Health Check | Failure Action |
|------------|--------------|----------------|
| PostgreSQL | Connection pool + simple query | Mark not ready, circuit breaker |
| Redis | PING command | Mark not ready, circuit breaker |
| Object Storage | HEAD bucket | Mark not ready, circuit breaker |

### 10.5 High Availability

**Database HA:**
- PostgreSQL with streaming replication (primary + replicas)
- Connection pooling (PgBouncer) for connection management
- Read replicas for query distribution
- Automatic failover with Patroni or similar

**Redis HA:**
- Redis Sentinel for automatic failover
- Redis Cluster for horizontal scaling (optional)
- Persistence enabled (RDB + AOF)
- Connection retry on failover

**Object Storage HA:**
- S3-compatible storage with built-in replication
- MinIO cluster mode for self-hosted deployments
- Cross-region replication for disaster recovery

**Configuration:**
```yaml
database:
  primary:
    host: "pg-primary.example.com"
    port: 5432
  replicas:
    - host: "pg-replica-1.example.com"
      port: 5432
    - host: "pg-replica-2.example.com"
      port: 5432
  pool:
    max_connections: 50
    max_idle: 10
    max_lifetime: 30m
  
redis:
  sentinel:
    enabled: true
    master: "qhronos-master"
    nodes:
      - "sentinel-1.example.com:26379"
      - "sentinel-2.example.com:26379"
      - "sentinel-3.example.com:26379"
  pool:
    max_connections: 100
    
object_storage:
  endpoint: "s3.example.com"
  region: "us-east-1"
  bucket: "qhronos"
  retry:
    max_attempts: 3
    base_delay: 100ms
```

### 10.6 Idempotency & Consistency

**Idempotency Keys:**
- All mutating API operations support idempotency keys
- Key stored in Redis with configurable TTL (default: 24 hours)
- Duplicate requests return cached response

**At-Least-Once Delivery:**
- Jobs may be executed more than once in failure scenarios
- Actions should be designed for idempotency
- Idempotency key passed to webhooks and integrations

**Consistency Guarantees:**

| Operation | Consistency | Notes |
|-----------|-------------|-------|
| Event CRUD | Strong | PostgreSQL transactions |
| Schedule creation | Eventual | Redis + PostgreSQL |
| Job creation | Strong | PostgreSQL transactions |
| Workflow state | Strong | PostgreSQL with row-level locking |
| File operations | Eventual | Object storage consistency model |

**Distributed Locking:**
```go
// Example: Distributed lock for schedule expansion
lock := redisLock.Obtain("expand:event:"+eventID, 30*time.Second)
if lock == nil {
    return // Another instance is processing
}
defer lock.Release()

// Safe to process event
expandEvent(event)
```

### 10.7 Backup & Disaster Recovery

**Backup Strategy:**

| Component | Backup Method | Frequency | Retention |
|-----------|---------------|-----------|-----------|
| PostgreSQL | pg_dump / WAL archiving | Continuous | 30 days |
| Redis | RDB snapshots + AOF | Every 5 min | 7 days |
| Object Storage | Cross-region replication | Continuous | Per policy |

**Recovery Procedures:**

1. **Point-in-Time Recovery (PostgreSQL):**
   - Restore base backup
   - Replay WAL to target time
   - Verify data integrity

2. **Redis Recovery:**
   - Restore from RDB snapshot
   - Replay AOF for recent changes
   - Re-expand events if schedules lost

3. **Full Disaster Recovery:**
   - Provision new infrastructure
   - Restore PostgreSQL from backup
   - Restore Redis from backup
   - Sync object storage from replica
   - Verify and resume operations

**RTO/RPO Targets:**

| Scenario | RTO | RPO |
|----------|-----|-----|
| Single node failure | < 1 minute | 0 (HA) |
| Database failure | < 5 minutes | < 1 minute |
| Redis failure | < 1 minute | < 5 minutes |
| Full region failure | < 1 hour | < 5 minutes |

### 10.8 Log Retention
- Jobs are retained based on configurable retention policy
- Consider partitioning jobs table by date for performance
- Implement job rotation/archival if needed for compliance
- Jobs serve as the primary audit trail
- Single unified jobs table simplifies querying and analysis

---

## 11. Planned Features

### 11.1 Workflow Enhancements
- **Visual Workflow Builder**: UI for creating workflows visually
- **Workflow Templates**: Pre-built workflow templates for common use cases
- **Workflow Versioning**: Version control for workflow definitions
- **Workflow Testing**: Test workflows with sample data before deployment
- **Workflow Metrics**: Detailed Prometheus metrics and Grafana dashboards for workflow execution
- **Event-Driven Workflows**: Trigger workflows on event patterns
- **Workflow Scheduling**: Schedule workflows like events
- **Workflow Notifications**: Notify on workflow completion/failure

### 11.2 Metrics & Reporting
- Enhanced Prometheus metrics and Grafana dashboards based on jobs
- Dashboard for event and workflow metrics
- Performance monitoring and alerting
- Cost tracking for LLM usage (via Prometheus metrics)
- Log analysis and insights
- Log viewer with hierarchical display (job → workflow → step → action)

### 11.3 Platform Enhancements
- Multi-tenant organization/user support
- Admin dashboard for event and system management
- Log viewer with hierarchical display and search
- Enhanced monitoring and observability
- Prometheus metrics export

### 11.4 Integration Enhancements
- Additional notification channels (email, SMS)
- More LLM providers
- Custom authentication providers
- Pluggable storage or queue backends
- Webhook HMAC signing validation improvements

### 11.5 Developer Experience
- SDKs for popular languages (Python, Node.js, etc.)
- CLI tool for workflow management
- Workflow debugging tools
- Enhanced error messages and diagnostics
- Log querying and filtering tools
- Log visualization with hierarchical view

---

## 12. Extension Points

### 12.1 Action Types
- New action types can be added without changing core dispatcher logic
- Action system designed for extensibility
- Examples: email, SMS, custom integrations

### 12.2 Authentication Providers
- Custom authentication providers can be integrated
- JWT and master token system can be extended

### 12.3 Storage Backends
- Pluggable storage backends for files
- Database abstraction allows for different SQL databases
- Redis abstraction allows for different queue backends

### 12.4 Script Modules
- Custom script modules can be added
- Module system supports extension
- Built-in modules can be extended

---

## 13. Go Library Integration

Qhronos can be embedded directly into Go applications as a library. The `pkg/qhronos` package provides:
- Programmatic event management
- Job tracking
- Token management
- Optional HTTP server
- Database migration support

See [embedding.md](../qhronos-server/docs/embedding.md) for detailed documentation.

---

## 14. Design Documents Reference

This section provides an overview of all design documents for Qhronos. Each document covers a specific aspect of the system in detail.

### 14.1 Workflow Design

**File**: [workflow-design.md](workflow-design.md)

**Summary**: Comprehensive design document for the workflow orchestration system. Covers:

- **Multi-step Workflows**: Sequential and parallel step execution
- **Step Types**: Action, condition, delay, sub-workflow, loop, and set_variable steps
- **Conditional Logic**: JavaScript-like expression evaluation for branching
- **Data Flow**: Variable management and template resolution
- **Error Handling**: Timeout configuration, retry strategies, and failure paths
- **Workflow Execution**: State management, step execution flow, and job creation
- **Database Schema**: Workflow definitions, instances, and step executions
- **API Design**: Workflow CRUD and execution endpoints

**Key Features**:
- Conditional branching with JavaScript-like expressions
- Loop constructs (while and foreach)
- Variable support for data sharing across steps
- Sub-workflow execution
- Timeout configuration per step
- Template resolution for dynamic values

### 14.2 Script Design

**File**: [script-design.md](script-design.md)

**Summary**: Detailed design document for the JavaScript script execution system. Covers:

- **Script Execution Model**: Synchronous execution in Goja runtime
- **Execution Context**: Direct access to input, steps, workflow variables, and console
- **Built-in APIs**: 
  - `fetch` for HTTP requests
  - `require()` for modules (crypto, uuid, validator, jsonpath, db, llm, files)
  - Database operations (MySQL and PostgreSQL)
  - LLM integration (OpenAI, Anthropic, Gemini, OpenRouter)
  - File operations (global, event, job, workflow scoped)
- **Module System**: Custom package support via require()
- **Security**: Sandboxed execution environment with restrictions
- **Error Handling**: Exception handling and error propagation
- **Variable Management**: Setting workflow variables from script output

**Key Features**:
- Synchronous JavaScript execution
- Database query support (MySQL/PostgreSQL)
- LLM API integration
- File system access with scoped paths
- Native JavaScript features (no lodash/moment dependencies)
- Console logging API

### 14.3 Client Design

**File**: [client-design.md](client-design.md)

**Summary**: Design specifications for client SDKs and CLI tools. Covers:

- **JavaScript/TypeScript SDK**: 
  - npm package (`qhronos-client`)
  - Type-safe API with full TypeScript definitions
  - Works in Node.js and browsers
  - Helper methods for polling and waiting
- **Python SDK**:
  - PyPI package (`qhronos-client`)
  - Sync and async clients
  - Type hints and Pydantic models
  - Context managers for resource cleanup
- **CLI Tool**:
  - Cross-platform command-line interface
  - Configuration file support
  - Multiple output formats (table, JSON, YAML)
  - Interactive shell mode
  - Job watching and streaming

**Key Features**:
- Consistent API across all clients
- Authentication handling (JWT/master token)
- Error handling with typed exceptions
- Retry logic with exponential backoff
- Request/response validation

### 14.4 Implementation Plan

**File**: [plan.md](../plans/plan.md)

**Summary**: Phased implementation plan for Qhronos v2. Covers:

- **Phase 1-8**: Transition from occurrences to jobs, remove archival, implement execution logging
- **Phase 9**: Workflow system implementation
- **Phase 10**: Script system implementation
- **Phase 11**: Testing for workflows and scripts
- **Phase 12**: Documentation updates

**Key Phases**:
1. Database schema changes (schedules, jobs)
2. Code refactoring (occurrences → jobs)
3. Event cleanup logic
4. API updates
5. Testing

### 14.5 Gap Analysis

**File**: [gap-analysis.md](../plans/gap-analysis.md)

**Summary**: Comprehensive gap analysis between current implementation and target design.

**Key Sections**:
1. Feature gap matrix (current vs target status)
2. Database schema changes required
3. Models, repositories, handlers gaps
4. New systems required (Workflow, Script, Integration, Storage)
5. API routes comparison
6. Dependencies and configuration gaps
7. Migration complexity assessment
8. Risk assessment and mitigation
9. Implementation priority and effort estimation

**Key Findings**:
- Core refactoring (occurrences → jobs): 5 weeks
- Workflow system: 3 weeks
- Script system: 3 weeks
- Integration system: 3 weeks
- File system: 2 weeks
- **Total estimated effort**: 16 weeks
6. Documentation updates
7. Migration strategy
8. Performance optimization
9-12. Workflow and script implementation

### 14.6 API Documentation

**File**: [api.md](../qhronos-server/docs/api.md)

**Summary**: REST API reference documentation. Covers:

- Event endpoints (CRUD operations)
- Job endpoints (querying and monitoring)
- Workflow endpoints (CRUD and execution)
- Script endpoints (CRUD and execution)
- Token management endpoints
- System endpoints (status, health)

### 14.7 Embedding Guide

**File**: [embedding.md](../qhronos-server/docs/embedding.md)

**Summary**: Guide for using Qhronos as a Go library. Covers:

- Programmatic event management
- Job tracking
- Token management
- Optional HTTP server
- Database migration support
- Integration examples

---

## 15. Summary

Qhronos is a comprehensive event scheduling and workflow orchestration platform that combines reliable event delivery with powerful workflow automation capabilities. The system is designed for:

- **Reliability**: Durable state, retry mechanisms, error handling
- **Scalability**: Stateless design, horizontal scaling support
- **Extensibility**: Plugin-based action system, modular architecture
- **Security**: Authentication, authorization, sandboxed script execution
- **Developer Experience**: Simple APIs, comprehensive documentation, Go library support
- **Auditability**: Comprehensive logging for all job executions with hierarchical structure

The platform supports both simple event scheduling and complex multi-step workflows with AI capabilities, making it suitable for a wide range of automation and orchestration use cases. Events and schedules are automatically cleaned up when done, while jobs provide a complete audit trail with detailed execution information accessible via `/jobs` and `/jobs/:id` endpoints. The unified job structure supports hierarchical logging (job → workflow → step → action) with type-specific fields for each job type.
