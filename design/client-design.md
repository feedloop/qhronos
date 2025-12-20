# Qhronos Client SDKs and CLI Design

## Overview
This document outlines the design for client SDKs and CLI tools for Qhronos, providing developer-friendly interfaces to the Qhronos REST API across multiple languages and platforms.

---

## 1. JavaScript/TypeScript Client SDK

### Overview
A TypeScript client SDK for Qhronos, intended for distribution via npm and usable in both Node.js and browser environments. The SDK provides a full-featured, type-safe, and developer-friendly interface to the Qhronos REST API.

### Distribution
- **Package Name**: `qhronos-client`
- **Platforms**: Node.js (v14+), Browser (ES6+)
- **Formats**: ESM and CJS
- **Registry**: npm

### Core Features
- Type-safe API with full TypeScript definitions
- Framework agnostic (uses Fetch API)
- Authentication handling (JWT/master token)
- Request/response interceptors
- Retry logic with exponential backoff
- Error handling with typed exceptions
- Helper methods for common workflows

### API Methods

#### Event Management
```typescript
createEvent(data: CreateEventRequest): Promise<Event>
getEvent(id: string): Promise<Event>
listEvents(params?: ListEventsParams): Promise<Event[]>
updateEvent(id: string, data: UpdateEventRequest): Promise<Event>
deleteEvent(id: string): Promise<void>
```

#### Job Management
```typescript
getJob(id: string): Promise<Job>
listJobs(params?: ListJobsParams): Promise<Job[]>
getJobChildren(id: string): Promise<Job[]>
getEventJobs(eventId: string, params?: ListJobsParams): Promise<Job[]>
```

#### Workflow Management
```typescript
createWorkflow(data: CreateWorkflowRequest): Promise<Workflow>
getWorkflow(id: string): Promise<Workflow>
listWorkflows(params?: ListWorkflowsParams): Promise<Workflow[]>
updateWorkflow(id: string, data: UpdateWorkflowRequest): Promise<Workflow>
deleteWorkflow(id: string): Promise<void>
executeWorkflow(id: string, params?: Record<string, any>): Promise<Job>
getWorkflowJobs(workflowId: string, params?: ListJobsParams): Promise<Job[]>
```

#### Script Management
```typescript
createScript(data: CreateScriptRequest): Promise<Script>
getScript(id: string): Promise<Script>
listScripts(params?: ListScriptsParams): Promise<Script[]>
updateScript(id: string, data: UpdateScriptRequest): Promise<Script>
deleteScript(id: string): Promise<void>
executeScript(id: string, params?: Record<string, any>): Promise<Job>
getScriptJobs(scriptId: string, params?: ListJobsParams): Promise<Job[]>
```

#### Authentication & Tokens
```typescript
setAuthToken(token: string): void
getAuthToken(): string | null
logout(): void
```

#### System & Monitoring
```typescript
getStatus(): Promise<SystemStatus>
getSchedules(params?: ListSchedulesParams): Promise<Schedule[]>
```

#### Helper Methods
```typescript
waitForJobStatus(id: string, status: JobStatus, timeoutMs?: number): Promise<Job>
waitForJobCompletion(id: string, timeoutMs?: number): Promise<Job>
pollJob(id: string, intervalMs?: number, timeoutMs?: number): Promise<Job>
```

### Example Usage

```typescript
import { QhronosClient } from 'qhronos-client';

const qhronos = new QhronosClient({
  baseUrl: 'https://api.qhronos.example.com',
  authToken: 'your-jwt-or-master-token',
});

// Create an event
const event = await qhronos.createEvent({
  name: 'Daily Report',
  start_time: '2024-06-01T09:00:00Z',
  action: {
    type: 'webhook',
    url: 'https://yourapp.com/webhook',
  },
  schedule: { frequency: 'daily' },
  tags: ['report'],
});

// Execute a workflow
const job = await qhronos.executeWorkflow('workflow-id', {
  userId: 123,
  action: 'process',
});

// Wait for job completion
const completedJob = await qhronos.waitForJobCompletion(job.id, 60000);

// Execute a script
const scriptJob = await qhronos.executeScript('script-id', {
  data: { key: 'value' },
});
```

### Type Definitions

```typescript
interface QhronosClientConfig {
  baseUrl: string;
  authToken?: string;
  timeout?: number;
  retries?: number;
}

interface CreateEventRequest {
  name: string;
  start_time: string;
  action: ActionConfig;
  schedule?: ScheduleConfig;
  tags?: string[];
}

interface CreateWorkflowRequest {
  name: string;
  description?: string;
  steps: WorkflowStep[];
  tags?: string[];
}

interface CreateScriptRequest {
  name: string;
  code: string;
  description?: string;
  tags?: string[];
}

interface Job {
  id: string;
  type: JobType;
  status: JobStatus;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  data: Record<string, any>;
}

type JobType = 'job' | 'workflow' | 'step' | 'api_call' | 'script' | 'webhook' | 'websocket' | 'llm';
type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
```

---

## 2. Python Client SDK

### Overview
A Python client SDK for Qhronos, providing a Pythonic interface to the Qhronos REST API with full type hints and async support.

### Distribution
- **Package Name**: `qhronos-client`
- **Python Version**: 3.8+
- **Registry**: PyPI

### Core Features
- Full type hints (PEP 484)
- Async/await support
- Sync and async clients
- Request/response models using Pydantic
- Automatic retry with exponential backoff
- Context managers for resource cleanup
- Rich error handling with custom exceptions

### API Methods

#### Event Management
```python
def create_event(data: CreateEventRequest) -> Event
def get_event(id: str) -> Event
def list_events(params: Optional[ListEventsParams] = None) -> List[Event]
def update_event(id: str, data: UpdateEventRequest) -> Event
def delete_event(id: str) -> None
```

#### Job Management
```python
def get_job(id: str) -> Job
def list_jobs(params: Optional[ListJobsParams] = None) -> List[Job]
def get_job_children(id: str) -> List[Job]
def get_event_jobs(event_id: str, params: Optional[ListJobsParams] = None) -> List[Job]
```

#### Workflow Management
```python
def create_workflow(data: CreateWorkflowRequest) -> Workflow
def get_workflow(id: str) -> Workflow
def list_workflows(params: Optional[ListWorkflowsParams] = None) -> List[Workflow]
def update_workflow(id: str, data: UpdateWorkflowRequest) -> Workflow
def delete_workflow(id: str) -> None
def execute_workflow(id: str, params: Optional[Dict[str, Any]] = None) -> Job
def get_workflow_jobs(workflow_id: str, params: Optional[ListJobsParams] = None) -> List[Job]
```

#### Script Management
```python
def create_script(data: CreateScriptRequest) -> Script
def get_script(id: str) -> Script
def list_scripts(params: Optional[ListScriptsParams] = None) -> List[Script]
def update_script(id: str, data: UpdateScriptRequest) -> Script
def delete_script(id: str) -> None
def execute_script(id: str, params: Optional[Dict[str, Any]] = None) -> Job
def get_script_jobs(script_id: str, params: Optional[ListJobsParams] = None) -> List[Job]
```

#### Authentication & Tokens
```python
def set_auth_token(token: str) -> None
def get_auth_token() -> Optional[str]
```

#### System & Monitoring
```python
def get_status() -> SystemStatus
def get_schedules(params: Optional[ListSchedulesParams] = None) -> List[Schedule]
```

#### Helper Methods
```python
def wait_for_job_status(id: str, status: JobStatus, timeout_ms: Optional[int] = None) -> Job
def wait_for_job_completion(id: str, timeout_ms: Optional[int] = None) -> Job
def poll_job(id: str, interval_ms: int = 1000, timeout_ms: Optional[int] = None) -> Job
```

### Example Usage

```python
from qhronos import QhronosClient

# Initialize client
client = QhronosClient(
    base_url='https://api.qhronos.example.com',
    auth_token='your-jwt-or-master-token'
)

# Create an event
event = client.create_event({
    'name': 'Daily Report',
    'start_time': '2024-06-01T09:00:00Z',
    'action': {
        'type': 'webhook',
        'url': 'https://yourapp.com/webhook',
    },
    'schedule': {'frequency': 'daily'},
    'tags': ['report'],
})

# Execute a workflow
job = client.execute_workflow('workflow-id', {
    'userId': 123,
    'action': 'process',
})

# Wait for job completion
completed_job = client.wait_for_job_completion(job.id, timeout_ms=60000)

# Execute a script
script_job = client.execute_script('script-id', {
    'data': {'key': 'value'},
})
```

### Async Example

```python
import asyncio
from qhronos import AsyncQhronosClient

async def main():
    async with AsyncQhronosClient(
        base_url='https://api.qhronos.example.com',
        auth_token='your-jwt-or-master-token'
    ) as client:
        # Create an event
        event = await client.create_event({
            'name': 'Daily Report',
            'start_time': '2024-06-01T09:00:00Z',
            'action': {
                'type': 'webhook',
                'url': 'https://yourapp.com/webhook',
            },
        })
        
        # Execute workflow
        job = await client.execute_workflow('workflow-id', {'userId': 123})
        
        # Wait for completion
        completed_job = await client.wait_for_job_completion(job.id)

asyncio.run(main())
```

### Type Definitions

```python
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel

class JobType(str, Enum):
    JOB = 'job'
    WORKFLOW = 'workflow'
    STEP = 'step'
    API_CALL = 'api_call'
    SCRIPT = 'script'
    WEBHOOK = 'webhook'
    WEBSOCKET = 'websocket'
    LLM = 'llm'

class JobStatus(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class Job(BaseModel):
    id: str
    type: JobType
    status: JobStatus
    started_at: str
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    data: Dict[str, Any]
```

---

## 3. CLI Tool

### Overview
A command-line interface tool for Qhronos, providing a convenient way to interact with the Qhronos API from the terminal.

### Distribution
- **Package Name**: `qhronos-cli`
- **Platforms**: Linux, macOS, Windows
- **Installation**: npm, pip, or standalone binaries
- **Registry**: npm, PyPI, GitHub Releases

### Core Features
- Interactive and non-interactive modes
- Configuration file support (`~/.qhronos/config.yaml`)
- Environment variable support
- Colored output with tables
- JSON output option
- Command completion (bash/zsh/fish)
- Streaming output for long-running operations

### Configuration

**Config File** (`~/.qhronos/config.yaml`):
```yaml
base_url: https://api.qhronos.example.com
auth_token: your-jwt-or-master-token
output_format: table  # table, json, yaml
default_timeout: 60000
```

**Environment Variables**:
```bash
QHRONOS_BASE_URL=https://api.qhronos.example.com
QHRONOS_AUTH_TOKEN=your-token
QHRONOS_OUTPUT_FORMAT=json
```

### Commands

#### Events
```bash
# Create event
qhronos events create --name "Daily Report" \
  --start-time "2024-06-01T09:00:00Z" \
  --action-type webhook \
  --action-url "https://yourapp.com/webhook" \
  --schedule-frequency daily \
  --tags report,daily

# List events
qhronos events list [--tags TAG1,TAG2] [--format json]

# Get event
qhronos events get EVENT_ID

# Update event
qhronos events update EVENT_ID --name "New Name"

# Delete event
qhronos events delete EVENT_ID

# List jobs for event
qhronos events jobs EVENT_ID [--status completed] [--limit 10]
```

#### Jobs
```bash
# Get job
qhronos jobs get JOB_ID

# List jobs
qhronos jobs list [--type workflow] [--status completed] [--limit 10]

# Get job children
qhronos jobs children JOB_ID

# Watch job (stream updates)
qhronos jobs watch JOB_ID [--timeout 60000]

# Wait for job completion
qhronos jobs wait JOB_ID [--timeout 60000]
```

#### Workflows
```bash
# Create workflow
qhronos workflows create --name "My Workflow" \
  --file workflow.json

# List workflows
qhronos workflows list [--tags TAG1,TAG2]

# Get workflow
qhronos workflows get WORKFLOW_ID

# Update workflow
qhronos workflows update WORKFLOW_ID --file workflow.json

# Delete workflow
qhronos workflows delete WORKFLOW_ID

# Execute workflow
qhronos workflows execute WORKFLOW_ID \
  --params '{"userId": 123, "action": "process"}'

# List workflow jobs
qhronos workflows jobs WORKFLOW_ID [--status completed]
```

#### Scripts
```bash
# Create script
qhronos scripts create --name "My Script" \
  --file script.js

# List scripts
qhronos scripts list [--tags TAG1,TAG2]

# Get script
qhronos scripts get SCRIPT_ID

# Update script
qhronos scripts update SCRIPT_ID --file script.js

# Delete script
qhronos scripts delete SCRIPT_ID

# Execute script
qhronos scripts execute SCRIPT_ID \
  --params '{"data": {"key": "value"}}'

# List script jobs
qhronos scripts jobs SCRIPT_ID [--status completed]
```

#### System & Monitoring
```bash
# Get system status
qhronos status

# List schedules
qhronos schedules list [--limit 10]

# Get schedule
qhronos schedules get SCHEDULE_ID
```

#### Configuration
```bash
# Set base URL
qhronos config set base_url https://api.qhronos.example.com

# Set auth token
qhronos config set auth_token your-token

# Get config
qhronos config get [key]

# List config
qhronos config list

# Remove config
qhronos config remove key
```

### Example Usage

```bash
# Initialize configuration
qhronos config set base_url https://api.qhronos.example.com
qhronos config set auth_token your-token

# Create an event
qhronos events create \
  --name "Daily Report" \
  --start-time "2024-06-01T09:00:00Z" \
  --action-type webhook \
  --action-url "https://yourapp.com/webhook" \
  --schedule-frequency daily

# Execute a workflow
qhronos workflows execute workflow-id \
  --params '{"userId": 123, "action": "process"}'

# Watch job progress
qhronos jobs watch job-id

# Get job details as JSON
qhronos jobs get job-id --format json | jq '.data.output'
```

### Interactive Mode

```bash
# Start interactive shell
qhronos shell

# In shell:
qhronos> events list
qhronos> workflows execute workflow-id --params '{"key": "value"}'
qhronos> jobs watch job-id
qhronos> exit
```

### Output Formats

**Table Format** (default):
```
┌─────────────┬──────────┬────────────┬─────────────────────────┐
│ ID          │ Type     │ Status     │ Started At              │
├─────────────┼──────────┼────────────┼─────────────────────────┤
│ job-123     │ workflow │ completed  │ 2024-06-01T09:00:00Z   │
│ job-456     │ script   │ running    │ 2024-06-01T09:01:00Z   │
└─────────────┴──────────┴────────────┴─────────────────────────┘
```

**JSON Format**:
```bash
qhronos jobs list --format json
```

**YAML Format**:
```bash
qhronos jobs list --format yaml
```

### Command Structure

```
qhronos [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGUMENTS]

Global Options:
  --base-url URL       Override base URL
  --auth-token TOKEN   Override auth token
  --format FORMAT      Output format (table, json, yaml)
  --config FILE        Config file path
  --verbose            Verbose output
  --quiet              Quiet output
  --version            Show version
  --help               Show help
```

### Error Handling

- Exit codes: 0 (success), 1 (error), 2 (usage error)
- Clear error messages with suggestions
- Stack traces in verbose mode
- JSON error output option

### Installation

**npm**:
```bash
npm install -g qhronos-cli
```

**pip**:
```bash
pip install qhronos-cli
```

**Standalone Binary**:
```bash
# Download from GitHub Releases
curl -L https://github.com/feedloop/qhronos-monorepo/releases/latest/download/qhronos-cli-linux-amd64 -o /usr/local/bin/qhronos
chmod +x /usr/local/bin/qhronos
```

---

## 4. Common Design Principles

### Authentication
- All clients support JWT tokens and master tokens
- Token can be set via constructor/config, environment variables, or methods
- Token is included in Authorization header: `Authorization: Bearer <token>`

### Error Handling
- Typed exceptions/errors for different error types
- HTTP status codes mapped to client exceptions
- Retry logic for transient errors (5xx, network errors)
- Clear error messages with context

### Request/Response
- All requests use JSON
- All responses are JSON
- Consistent error response format
- Request/response validation

### Rate Limiting
- Respect rate limit headers
- Automatic retry with exponential backoff
- Configurable retry behavior

### Timeouts
- Configurable request timeouts
- Default timeout: 30 seconds
- Long-running operations (wait/poll) have separate timeout configs

### Logging
- Configurable logging levels
- Request/response logging in debug mode
- No sensitive data in logs (tokens, passwords)

---

## 5. Implementation Status

- [ ] JavaScript/TypeScript SDK
- [ ] Python SDK
- [ ] CLI Tool
- [ ] Documentation
- [ ] Examples
- [ ] Tests
- [ ] CI/CD pipelines
- [ ] Package publishing
