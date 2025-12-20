# Qhronos Workflow System Design

## 1. Overview

The Workflow System extends Qhronos to support multi-step, conditional, and parallel execution of actions. It enables users to define complex automation workflows that can chain events, handle conditional logic, manage state, and orchestrate multiple actions.

### Core Concepts

- **Workflow**: A reusable definition of steps and their execution logic
- **Workflow Instance**: A running execution of a workflow definition
- **Step**: A single unit of work in a workflow (action, condition, delay, sub-workflow)
- **Step Execution**: The actual execution of a step within a workflow instance
- **Workflow State**: The current status and data of a workflow instance

### Key Features

1. **Sequential & Parallel Execution**: Steps can execute in sequence or parallel
2. **Conditional Logic**: If/then/else branching based on step outputs
3. **Data Flow**: Pass data between steps using variables
4. **Error Handling**: Retry strategies and error handling per step
5. **Sub-workflows**: Nest workflows within workflows
6. **Event Integration**: Trigger workflows from events or schedule them
7. **State Persistence**: Durable workflow state in PostgreSQL

---

## 2. Architecture

### High-Level Architecture

```
[Workflow Definition] (PostgreSQL)
         │
         ▼
[Workflow Engine] ──► [Step Executor] ──► [Action System]
         │                    │                    │
         │                    ▼                    ▼
         │            [Condition Evaluator]   [Webhook/WS/API]
         │                    │
         ▼                    ▼
[State Manager] ──► [Redis Queue] ──► [Workflow Dispatcher]
         │
         ▼
[PostgreSQL State]
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Workflow Engine** | Orchestrates workflow execution, manages step lifecycle |
| **Step Executor** | Executes individual steps (actions, conditions, delays) |
| **State Manager** | Persists and retrieves workflow instance state |
| **Workflow Dispatcher** | Processes workflow instances from Redis queue |
| **Condition Evaluator** | Evaluates JavaScript-like conditional expressions for branching |
| **Action System** | Reuses existing action executors (webhook, websocket, apicall) |

---

## 3. Data Model

### Workflow Definition

```sql
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    definition JSONB NOT NULL, -- WorkflowDefinition structure
    version INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'active', -- active, inactive, archived
    tags TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ,
    created_by TEXT,
    
    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'archived'))
);

CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_tags ON workflows USING GIN(tags);
```

### Workflow Instance

```sql
CREATE TABLE workflow_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    workflow_version INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, running, completed, failed, cancelled
    input_data JSONB NOT NULL DEFAULT '{}', -- Initial input data
    output_data JSONB, -- Final output data
    variables JSONB NOT NULL DEFAULT '{}', -- Workflow-level variables (mutable during execution)
    current_step_id TEXT, -- Current step being executed
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_workflow_instances_workflow_id ON workflow_instances(workflow_id);
CREATE INDEX idx_workflow_instances_status ON workflow_instances(status);
CREATE INDEX idx_workflow_instances_created_at ON workflow_instances(created_at);
```

### Step Execution

```sql
CREATE TABLE workflow_step_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instance_id UUID NOT NULL REFERENCES workflow_instances(id) ON DELETE CASCADE,
    step_id TEXT NOT NULL, -- Step ID from workflow definition
    step_type TEXT NOT NULL, -- action, condition, delay, loop, sub_workflow, set_variable
    status TEXT NOT NULL DEFAULT 'pending', -- pending, running, completed, failed, skipped
    input_data JSONB, -- Step input data
    output_data JSONB, -- Step output data
    error_message TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    loop_iteration INTEGER,  -- Current iteration number for loop steps
    loop_context JSONB,  -- Loop context (variables, previous outputs, etc.)
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),
    CONSTRAINT valid_step_type CHECK (step_type IN ('action', 'condition', 'delay', 'loop', 'sub_workflow', 'set_variable'))
);

CREATE INDEX idx_step_executions_instance_id ON workflow_step_executions(instance_id);
CREATE INDEX idx_step_executions_step_id ON workflow_step_executions(instance_id, step_id);
CREATE INDEX idx_step_executions_status ON workflow_step_executions(status);
```

### Scripts Repository

Scripts are stored JavaScript code that can be executed via script action type.

```sql
CREATE TABLE scripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    code TEXT NOT NULL, -- JavaScript code
    version INTEGER NOT NULL DEFAULT 1,
    language TEXT NOT NULL DEFAULT 'javascript', -- For future extensibility (javascript, typescript, etc.)
    tags TEXT[] NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active', -- active, inactive, archived
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    
    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'archived')),
    CONSTRAINT valid_language CHECK (language IN ('javascript'))
);

CREATE INDEX idx_scripts_name ON scripts(name);
CREATE INDEX idx_scripts_status ON scripts(status);
CREATE INDEX idx_scripts_tags ON scripts USING GIN(tags);
CREATE UNIQUE INDEX idx_scripts_name_version ON scripts(name, version);
```

**Script Execution Context:**
Scripts receive a context object with properties accessible directly (without `context.` prefix):
- `input`: Input data from workflow instance or previous step (access as `input` or `context.input`)
- `steps`: Object containing outputs from previous steps (e.g., `steps.step1.output` or `context.steps.step1.output`)
- `workflow`: Workflow-level variables (access as `workflow` or `context.workflow`)
- `console`: Console object for logging (console.log, console.error, etc.)
- `require`: Module system (optional, for future extension)

**Script Return Value:**
Scripts should return a value that becomes the step output:
- Return object: `{ success: true, data: {...} }`
- Return primitive: Automatically wrapped in `{ value: <primitive> }`
- Throw error: Caught and step marked as failed

---

## 4. Workflow Definition Structure

### JSON Schema

```json
{
  "version": "1.0",
  "name": "Example Workflow",
  "description": "A sample workflow",
  "steps": [
    {
      "id": "step1",
      "type": "action",
      "name": "Call API",
      "action": {
        "type": "apicall",
        "params": {
          "method": "POST",
          "url": "https://api.example.com/endpoint",
          "headers": {
            "Authorization": "Bearer {{token}}"
          },
          "body": {
            "data": "{{input.data}}"
          }
        }
      },
      "timeout": "30s",
      "on_success": "step2",
      "on_failure": "step_error_handler",
      "retry": {
        "max_attempts": 3,
        "backoff": "exponential",
        "initial_delay": "1s"
      }
    },
    {
      "id": "step2",
      "type": "condition",
      "name": "Check Response",
      "condition": "step1.output.status_code === 200 && step1.output.success === true",
      "on_true": "step3",
      "on_false": "step_failure"
    },
    {
      "id": "step3",
      "type": "action",
      "name": "Send Notification",
      "action": {
        "type": "webhook",
        "params": {
          "url": "https://webhook.example.com/notify"
        }
      },
      "timeout": "15s",
      "parallel": ["step4"]
    },
    {
      "id": "step4",
      "type": "delay",
      "name": "Wait 5 minutes",
      "duration": "5m"
    },
    {
      "id": "step5",
      "type": "action",
      "name": "Process Data with Script",
      "action": {
        "type": "script",
        "params": {
          "script_name": "process-data",
          "input": {
            "apiResponse": "{{step1.output}}",
            "notificationSent": "{{step3.output}}"
          }
        }
      },
      "timeout": "30s",
      "on_success": "step6",
      "on_failure": "step_error_handler"
    },
    {
      "id": "step6",
      "type": "action",
      "name": "Generate Summary with LLM",
      "action": {
        "type": "llm",
        "params": {
          "provider": "openai",
          "model": "gpt-4-turbo-preview",
          "messages": [
            {
              "role": "system",
              "content": "You are a helpful assistant that summarizes data."
            },
            {
              "role": "user",
              "content": "Summarize the following data: {{step5.output.data}}"
            }
          ],
          "temperature": 0.7,
          "max_tokens": 500,
          "api_key": "{{env.OPENAI_API_KEY}}"
        }
      },
      "timeout": "60s",
      "on_success": "step7",
      "on_failure": "step_error_handler"
    },
    {
      "id": "step7",
      "type": "sub_workflow",
      "name": "Run Sub-workflow",
      "workflow_id": "{{workflow_id}}",
      "input": {
        "data": "{{step6.output}}"
      }
    }
  ],
  "variables": {
    "token": "{{env.API_TOKEN}}"
  },
  "error_handler": {
    "step_id": "step_error_handler",
    "action": {
      "type": "webhook",
      "params": {
        "url": "https://webhook.example.com/error"
      }
    }
  }
}
```

### Step Types

#### 1. Action Step
Executes an action (webhook, websocket, apicall, script, llm).

```json
{
  "id": "step_action",
  "type": "action",
  "name": "Step Name",
  "action": {
    "type": "webhook|websocket|apicall|script|llm",
    "params": { ... }
  },
  "timeout": "30s|5m|1h",  // Optional: timeout for step execution (default: 10s for webhook/apicall/script, 60s for llm, no timeout for websocket)
  "on_success": "next_step_id",
  "on_failure": "error_step_id",
  "retry": { ... }
}
```

**Action Types:**

- **webhook**: Delivers event to HTTP endpoint
- **websocket**: Delivers event to connected WebSocket client
- **apicall**: Makes generic HTTP request with custom method, headers, body
- **script**: Executes JavaScript code from scripts repository
- **llm**: Calls Large Language Model API (OpenAI, Anthropic, Gemini, OpenRouter)
- **db**: Executes database queries (MySQL, PostgreSQL) via integration
- **spreadsheet**: Reads/writes Google Sheets data via integration
- **notification**: Sends notifications via channels (SES, Twilio, Slack, Discord, Telegram)

**Timeout Configuration:**
- `timeout` (optional): Maximum duration for step execution
  - Format: Duration string (e.g., "30s", "5m", "1h")
  - Default: 10s for webhook/apicall/script actions, 60s for llm actions, no timeout for websocket actions
  - If timeout is exceeded, step is marked as failed and `on_failure` is triggered
  - Timeout applies per retry attempt

**Script Action Parameters:**

```json
{
  "type": "script",
  "params": {
    "script_id": "uuid",  // Reference to script in scripts repository
    "script_name": "script-name",  // Alternative: reference by name (uses latest version)
    "script_version": 1,  // Optional: specific version (if using script_name)
    "input": {  // Optional: override input data
      "key": "value"
    }
  }
}
```

**Script Example:**

```javascript
// Script: process-data.js
// Receives input data and previous step outputs
// All context properties are accessible directly
const previousStep = steps.step1.output;

// Process data
const processed = {
  userId: input.userId,
  status: previousStep.status,
  timestamp: Date.now(),
  processed: true
};

// Transform or validate data
if (processed.status !== 'success') {
  throw new Error('Previous step did not succeed');
}

// Return result (becomes step output)
return {
  success: true,
  data: processed,
  message: 'Data processed successfully'
};
```

**LLM Action Parameters:**

The LLM action supports multiple providers: OpenAI, Anthropic, Gemini, and OpenRouter.

```json
{
  "type": "llm",
  "params": {
    "provider": "openai|anthropic|gemini|openrouter",
    "model": "gpt-4|claude-3-opus|gemini-pro|...",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "{{input.question}}"
      }
    ],
    "temperature": 0.7,  // Optional: 0.0 to 2.0
    "max_tokens": 1000,  // Optional: maximum tokens in response
    "api_key": "{{env.OPENAI_API_KEY}}",  // Optional: can use env variable or workflow variable
    "stream": false,  // Optional: enable streaming (default: false)
    "base_url": "https://api.openai.com/v1"  // Optional: custom base URL (for OpenRouter or custom endpoints)
  }
}
```

**Provider-Specific Parameters:**

**OpenAI:**
```json
{
  "type": "llm",
  "params": {
    "provider": "openai",
    "model": "gpt-4-turbo-preview",
    "messages": [
      { "role": "user", "content": "Hello!" }
    ],
    "temperature": 0.7,
    "max_tokens": 500,
    "api_key": "{{env.OPENAI_API_KEY}}"
  }
}
```

**Anthropic:**
```json
{
  "type": "llm",
  "params": {
    "provider": "anthropic",
    "model": "claude-3-opus-20240229",
    "messages": [
      { "role": "user", "content": "Hello!" }
    ],
    "temperature": 0.7,
    "max_tokens": 1000,
    "api_key": "{{env.ANTHROPIC_API_KEY}}"
  }
}
```

**Gemini (Google):**
```json
{
  "type": "llm",
  "params": {
    "provider": "gemini",
    "model": "gemini-pro",
    "messages": [
      { "role": "user", "content": "Hello!" }
    ],
    "temperature": 0.7,
    "max_tokens": 1000,
    "api_key": "{{env.GEMINI_API_KEY}}"
  }
}
```

**OpenRouter:**
```json
{
  "type": "llm",
  "params": {
    "provider": "openrouter",
    "model": "openai/gpt-4-turbo",
    "messages": [
      { "role": "user", "content": "Hello!" }
    ],
    "temperature": 0.7,
    "max_tokens": 1000,
    "api_key": "{{env.OPENROUTER_API_KEY}}",
    "base_url": "https://openrouter.ai/api/v1"  // Optional, defaults to OpenRouter URL
  }
}
```

**LLM Response Format:**

The LLM action returns a standardized response:

```json
{
  "provider": "openai",
  "model": "gpt-4-turbo-preview",
  "content": "The generated text response...",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  },
  "finish_reason": "stop"
}
```

**Supported Models:**

- **OpenAI**: gpt-4, gpt-4-turbo-preview, gpt-3.5-turbo, etc.
- **Anthropic**: claude-3-opus-20240229, claude-3-sonnet-20240229, claude-3-haiku-20240307, etc.
- **Gemini**: gemini-pro, gemini-pro-vision, etc.
- **OpenRouter**: Any model available on OpenRouter (e.g., "openai/gpt-4", "anthropic/claude-3-opus", etc.)

**Database Action Parameters:**

The `db` action type executes database queries via configured database integrations.

```json
{
  "type": "db",
  "params": {
    "integration_id": "uuid",  // Reference to database integration
    "operation": "query|execute",  // query for SELECT, execute for INSERT/UPDATE/DELETE
    "sql": "SELECT * FROM users WHERE status = ?",
    "params": ["active"],  // SQL parameters (positional)
    "transaction": false  // Optional: wrap in transaction (default: false)
  }
}
```

**Database Action Examples:**

**SELECT Query:**
```json
{
  "id": "fetch_users",
  "type": "action",
  "name": "Fetch Active Users",
  "action": {
    "type": "db",
    "params": {
      "integration_id": "mysql-prod-id",
      "operation": "query",
      "sql": "SELECT id, name, email FROM users WHERE status = ? LIMIT ?",
      "params": ["active", 100]
    }
  },
  "next": "process_users"
}
```

**INSERT Query:**
```json
{
  "id": "insert_record",
  "type": "action",
  "name": "Insert Record",
  "action": {
    "type": "db",
    "params": {
      "integration_id": "postgres-prod-id",
      "operation": "execute",
      "sql": "INSERT INTO logs (event_id, message, created_at) VALUES ($1, $2, NOW())",
      "params": ["{{input.eventId}}", "{{steps.process.output.message}}"]
    }
  }
}
```

**Database Response Format:**

For `query` operations:
```json
{
  "rows": [
    {"id": 1, "name": "John", "email": "john@example.com"},
    {"id": 2, "name": "Jane", "email": "jane@example.com"}
  ],
  "row_count": 2
}
```

For `execute` operations:
```json
{
  "rows_affected": 1,
  "last_insert_id": 123  // MySQL only
}
```

**Spreadsheet Action Parameters:**

The `spreadsheet` action type reads/writes Google Sheets data via configured spreadsheet integrations.

```json
{
  "type": "spreadsheet",
  "params": {
    "integration_id": "uuid",  // Reference to Google Sheets integration
    "operation": "get|set|append|clear|batch_get|batch_set",
    "spreadsheet_id": "abc123",  // Google Sheets spreadsheet ID (optional if default set in integration)
    "range": "Sheet1!A1:D10",  // A1 notation range
    "values": [["a", "b"], ["c", "d"]]  // For set/append operations
  }
}
```

**Spreadsheet Operations:**

| Operation | Description | Required Params |
|-----------|-------------|-----------------|
| `get` | Read values from range | `range` |
| `set` | Write values to range | `range`, `values` |
| `append` | Append rows to range | `range`, `values` |
| `clear` | Clear values in range | `range` |
| `batch_get` | Read multiple ranges | `ranges` (array) |
| `batch_set` | Write to multiple ranges | `data` (array of {range, values}) |

**Spreadsheet Action Examples:**

**Read from Sheet:**
```json
{
  "id": "read_data",
  "type": "action",
  "name": "Read Sales Data",
  "action": {
    "type": "spreadsheet",
    "params": {
      "integration_id": "gsheets-prod-id",
      "operation": "get",
      "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
      "range": "Sales!A2:E100"
    }
  },
  "next": "process_sales"
}
```

**Write to Sheet:**
```json
{
  "id": "write_report",
  "type": "action",
  "name": "Write Report",
  "action": {
    "type": "spreadsheet",
    "params": {
      "integration_id": "gsheets-prod-id",
      "operation": "set",
      "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
      "range": "Report!A1",
      "values": [
        ["Date", "Total", "Status"],
        ["{{input.date}}", "{{steps.calculate.output.total}}", "Completed"]
      ]
    }
  }
}
```

**Append Rows:**
```json
{
  "id": "append_log",
  "type": "action",
  "name": "Append Log Entry",
  "action": {
    "type": "spreadsheet",
    "params": {
      "integration_id": "gsheets-prod-id",
      "operation": "append",
      "range": "Logs!A:D",
      "values": [
        ["{{input.timestamp}}", "{{input.eventType}}", "{{input.userId}}", "{{input.message}}"]
      ]
    }
  }
}
```

**Spreadsheet Response Format:**

For `get` operations:
```json
{
  "values": [
    ["Name", "Email", "Score"],
    ["Alice", "alice@example.com", "95"],
    ["Bob", "bob@example.com", "88"]
  ],
  "range": "Sheet1!A1:C3",
  "row_count": 3,
  "column_count": 3
}
```

For `set`/`append` operations:
```json
{
  "updated_range": "Sheet1!A1:C2",
  "updated_rows": 2,
  "updated_columns": 3,
  "updated_cells": 6
}
```

**Notification Action Parameters:**

The `notification` action type sends notifications via configured notification channel integrations.

```json
{
  "type": "notification",
  "params": {
    "integration_id": "uuid",  // Reference to notification integration
    "channel": "email|sms|slack|discord|telegram",
    // Channel-specific params below
  }
}
```

**Email (Amazon SES):**
```json
{
  "type": "notification",
  "params": {
    "integration_id": "ses-prod-id",
    "channel": "email",
    "to": ["user@example.com"],
    "cc": ["manager@example.com"],  // Optional
    "bcc": [],  // Optional
    "subject": "Workflow Completed: {{workflow.name}}",
    "body": "The workflow has completed successfully.\n\nDetails:\n- Event: {{input.eventName}}\n- Status: {{steps.process.output.status}}",
    "html": "<h1>Workflow Completed</h1><p>Status: {{steps.process.output.status}}</p>",  // Optional: HTML body
    "from": "noreply@example.com"  // Optional: override default sender
  }
}
```

**SMS (Twilio):**
```json
{
  "type": "notification",
  "params": {
    "integration_id": "twilio-prod-id",
    "channel": "sms",
    "to": "+1234567890",
    "body": "Alert: {{input.alertType}} - {{steps.check.output.message}}"
  }
}
```

**Slack:**
```json
{
  "type": "notification",
  "params": {
    "integration_id": "slack-prod-id",
    "channel": "slack",
    "webhook_url": "https://hooks.slack.com/...",  // Optional: override integration default
    "channel_name": "#alerts",  // Optional: for Bot API
    "text": "Workflow Alert",
    "blocks": [  // Optional: Slack Block Kit
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*Workflow Completed*\n• Event: {{input.eventName}}\n• Status: :white_check_mark: Success"
        }
      }
    ],
    "attachments": []  // Optional: legacy attachments
  }
}
```

**Discord:**
```json
{
  "type": "notification",
  "params": {
    "integration_id": "discord-prod-id",
    "channel": "discord",
    "content": "Workflow notification",
    "embeds": [
      {
        "title": "Workflow Completed",
        "description": "Event {{input.eventName}} processed successfully",
        "color": 5763719,
        "fields": [
          {"name": "Status", "value": "{{steps.process.output.status}}", "inline": true},
          {"name": "Duration", "value": "{{steps.process.output.duration}}ms", "inline": true}
        ]
      }
    ]
  }
}
```

**Telegram:**
```json
{
  "type": "notification",
  "params": {
    "integration_id": "telegram-prod-id",
    "channel": "telegram",
    "chat_id": "123456789",
    "text": "Workflow Alert: {{input.alertType}}\n\nDetails: {{steps.check.output.message}}",
    "parse_mode": "Markdown",  // Optional: Markdown or HTML
    "disable_notification": false  // Optional: silent notification
  }
}
```

**Notification Response Format:**

```json
{
  "provider": "ses|twilio|slack|discord|telegram",
  "success": true,
  "message_id": "provider-specific-id",  // Optional
  "metadata": {
    // Provider-specific response data
  }
}
```

**Notification Action Examples in Workflows:**

```json
{
  "id": "notify_success",
  "type": "action",
  "name": "Send Success Notification",
  "action": {
    "type": "notification",
    "params": {
      "integration_id": "slack-alerts-id",
      "channel": "slack",
      "text": "✅ Workflow completed successfully",
      "blocks": [
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": "*Workflow: {{workflow.name}}*\nCompleted at: {{input.timestamp}}"
          }
        }
      ]
    }
  }
}
```

```json
{
  "id": "alert_failure",
  "type": "action",
  "name": "Alert on Failure",
  "action": {
    "type": "notification",
    "params": {
      "integration_id": "ses-alerts-id",
      "channel": "email",
      "to": ["oncall@example.com"],
      "subject": "🚨 Workflow Failed: {{workflow.name}}",
      "html": "<h1>Workflow Failure Alert</h1><p>Error: {{steps.failed_step.output.error}}</p>"
    }
  }
}
```

#### 2. Condition Step
Evaluates a JavaScript-like condition expression and branches execution.

```json
{
  "id": "step_condition",
  "type": "condition",
  "name": "Check Condition",
  "condition": "step1.output.status_code === 200 && step1.output.data.length > 0",
  "on_true": "step_if_true",
  "on_false": "step_if_false"
}
```

**Condition Syntax:**
Conditions use JavaScript-like expressions with the following features:

- **Variable Access**: Use step IDs to access step outputs (e.g., `step1.output`, `step2.output.data`)
- **Property Access**: Use dot notation (e.g., `step1.output.status_code`) or bracket notation (e.g., `step1.output['status_code']`)
- **Comparison Operators**: 
  - `===` (strict equality)
  - `==` (loose equality)
  - `!==` (strict inequality)
  - `!=` (loose inequality)
  - `>` (greater than)
  - `<` (less than)
  - `>=` (greater than or equal)
  - `<=` (less than or equal)
- **Logical Operators**:
  - `&&` (AND)
  - `||` (OR)
  - `!` (NOT)
- **Type Checking**:
  - `typeof step1.output === 'string'`
  - `Array.isArray(step1.output.data)`
  - `step1.output !== null && step1.output !== undefined`
- **Array/Object Operations**:
  - `step1.output.items.length > 0`
  - `step1.output.items.includes('value')`
  - `step1.output.items.indexOf('value') !== -1`
  - `Object.keys(step1.output).length > 0`
- **Nested Property Access**:
  - `step1.output.user.profile.email`
  - `step1.output.results[0].status`
- **Input Data Access**:
  - `input.userId`
  - `input.data.items.length`
- **Workflow Variables**:
  - `workflow.variableName`
- **Complex Expressions**:
  - `(step1.output.status === 'success' || step1.output.status === 'completed') && step1.output.count > 10`
  - `!step1.output.error && step2.output.valid === true`
  - `step1.output.timestamp > Date.now() - 3600000` // Check if timestamp is within last hour

**Examples:**

```json
// Simple comparison
"condition": "step1.output.status_code === 200"

// Multiple conditions with AND
"condition": "step1.output.success === true && step1.output.data.length > 0"

// Multiple conditions with OR
"condition": "step1.output.status === 'success' || step1.output.status === 'completed'"

// Negation
"condition": "!step1.output.error"

// Type checking
"condition": "typeof step1.output.data === 'object' && step1.output.data !== null"

// Array operations
"condition": "Array.isArray(step1.output.items) && step1.output.items.length > 0"

// Nested property access
"condition": "step1.output.user.profile.active === true"

// Complex expression
"condition": "(step1.output.status === 'success' && step2.output.valid === true) || input.force === true"

// Checking multiple steps
"condition": "step1.output.status_code === 200 && step2.output.processed === true && step3.output.sent === true"
```

#### 3. Set Variable Step
Sets or updates workflow-level variables.

```json
{
  "id": "step_set_var",
  "type": "set_variable",
  "name": "Set API Token",
  "variables": {
    "apiToken": "{{step1.output.token}}",
    "userId": "{{input.userId}}",
    "timestamp": "{{step2.output.created_at}}"
  },
  "on_success": "next_step_id"
}
```

**Variable Assignment:**
- Variables can be set from:
  - Input data: `{{input.key}}`
  - Step outputs: `{{step_id.output.key}}`
  - Other variables: `{{workflow.existingVar}}`
  - Environment variables: `{{env.VAR_NAME}}`
  - Literal values: `"static_value"`
- Variables persist throughout the workflow instance execution
- Variables can be updated multiple times (later assignments override earlier ones)
- Variables are accessible in:
  - Template strings: `{{workflow.variableName}}`
  - Condition expressions: `workflow.variableName`
  - Scripts: `workflow.variableName` (direct access) or `context.workflow.variableName`

**Example:**
```json
{
  "id": "step_init",
  "type": "set_variable",
  "name": "Initialize Variables",
  "variables": {
    "retryCount": 0,
    "maxRetries": 3,
    "baseUrl": "https://api.example.com",
    "apiKey": "{{env.API_KEY}}"
  }
}
```

#### 4. Delay Step
Waits for a specified duration.

```json
{
  "id": "step_delay",
  "type": "delay",
  "name": "Wait",
  "duration": "5m|30s|1h"
}
```

#### 5. Loop Step
Iterates over a collection or repeats until a condition is met. Essential for agentic AI workflows that require iterative refinement, multi-step reasoning, or processing multiple items.

The loop type is determined automatically:
- If `condition` is provided → **While Loop** (repeat until condition is false)
- If `items` is provided → **ForEach Loop** (iterate over array)

**While Loop** - Repeat until condition is false:
```json
{
  "id": "step_loop",
  "type": "loop",
  "name": "Iterate Until Complete",
  "condition": "loop.iteration < 10 && step_agent.output.status !== 'complete'",
  "max_iterations": 10,  // Safety limit to prevent infinite loops
  "steps": [
    {
      "id": "step_agent",
      "type": "action",
      "name": "AI Agent Step",
      "action": {
        "type": "llm",
        "params": {
          "provider": "openai",
          "model": "gpt-4",
          "messages": [
            {
              "role": "system",
              "content": "You are an AI agent. Continue reasoning until you reach a conclusion."
            },
            {
              "role": "user",
              "content": "Previous reasoning: {{loop.previous_output.content}}\nContinue:"
            }
          ]
        }
      }
    }
  ],
  "on_complete": "next_step_id",
  "on_max_iterations": "step_timeout_handler"  // Optional: handle max iterations reached
}
```

**ForEach Loop** - Iterate over an array:
```json
{
  "id": "step_loop",
  "type": "loop",
  "name": "Process Each Item",
  "items": "{{step1.output.items}}",  // Array to iterate over
  "item_variable": "current_item",  // Variable name for current item in loop
  "index_variable": "loop_index",  // Optional: variable name for current index
  "max_iterations": 100,  // Safety limit
  "steps": [
    {
      "id": "step_process",
      "type": "action",
      "name": "Process Item",
      "action": {
        "type": "llm",
        "params": {
          "provider": "openai",
          "model": "gpt-4",
          "messages": [
            {
              "role": "user",
              "content": "Process this item: {{loop.current_item}}"
            }
          ]
        }
      }
    }
  ],
  "on_complete": "next_step_id",
  "on_max_iterations": "step_timeout_handler"
}
```

**Loop Context Variables:**

Within loop steps, the following variables are available:

- `loop.iteration`: Current iteration number (0-indexed)
- `loop.iteration_count`: Current iteration number (1-indexed)
- `loop.is_first`: Boolean, true if first iteration
- `loop.is_last`: Boolean, true if last iteration (foreach loops only)
- `loop.current_item`: Current item value (foreach loops only)
- `loop.loop_index`: Current index (foreach loops only)
- `loop.previous_output`: Output from previous iteration's last step
- `loop.all_outputs`: Array of all outputs from previous iterations
- `loop.break`: Function to break out of loop early
- `loop.continue`: Function to skip to next iteration

**Break and Continue:**

Steps within a loop can signal break/continue using special output:

```json
{
  "break": true,  // Break out of loop
  "continue": true,  // Skip to next iteration
  "output": { ... }  // Normal output
}
```

**Loop Output:**

The loop step aggregates outputs from all iterations:

```json
{
  "iterations": 5,
  "completed": true,
  "outputs": [
    { "iteration": 0, "output": { ... } },
    { "iteration": 1, "output": { ... } },
    ...
  ],
  "final_output": { ... }  // Output from last iteration
}
```

**Agentic AI Example:**

```json
{
  "id": "step_agentic_loop",
  "type": "loop",
  "name": "Agentic Reasoning Loop",
  "loop_type": "while",
  "condition": "step_agent.output.status !== 'complete' && step_agent.output.needs_more_info !== true",
  "max_iterations": 5,
  "steps": [
    {
      "id": "step_agent",
      "type": "action",
      "name": "AI Agent Reasoning",
      "action": {
        "type": "llm",
        "params": {
          "provider": "openai",
          "model": "gpt-4",
          "messages": [
            {
              "role": "system",
              "content": "You are an AI agent. Analyze the problem step by step. Return status: 'thinking', 'complete', or 'needs_more_info'."
            },
            {
              "role": "user",
              "content": "Problem: {{input.problem}}\nPrevious reasoning: {{loop.previous_output.content || 'None'}}\nContinue your analysis:"
            }
          ]
        }
      }
    },
    {
      "id": "step_check",
      "type": "condition",
      "name": "Check if Complete",
      "condition": "step_agent.output.status === 'complete'",
      "on_true": "loop.break",  // Special: break out of loop
      "on_false": "continue"  // Continue to next iteration
    }
  ],
  "on_complete": "step_finalize",
  "on_max_iterations": "step_timeout_handler"
}
```

#### 5. Sub-workflow Step
Executes another workflow as a step.

```json
{
  "id": "step_subworkflow",
  "type": "sub_workflow",
  "name": "Run Sub-workflow",
  "workflow_id": "uuid-or-{{variable}}",
  "input": {
    "key": "{{previous_step.output}}"
  }
}
```

---

## 5. Execution Flow

### Workflow Instance Lifecycle

1. **Creation**: Workflow instance created with input data
2. **Queuing**: Instance added to Redis queue for processing
3. **Execution**: Workflow dispatcher picks up instance
4. **Step Execution**: Steps executed according to definition
5. **State Updates**: State persisted after each step
6. **Completion**: Instance marked as completed/failed

### Step Execution Flow

```
1. Load step definition
2. Resolve variables/templates in step config
3. Parse timeout configuration (if specified)
4. Execute step based on type with timeout context:
   - Action: Execute via ActionsManager with timeout
     * Create context with timeout deadline
     * Execute action within timeout window
     * For script actions: Load script from repository, prepare execution context (including workflow variables), execute in Goja runtime
     * Cancel execution if timeout exceeded
   - Condition: Evaluate JavaScript-like expression (no timeout, fast operation)
     * Resolve variables (step outputs, input data, workflow variables)
     * Evaluate expression using JavaScript-like syntax
     * Support comparison operators (===, ==, !==, !=, >, <, >=, <=)
     * Support logical operators (&&, ||, !)
     * Support type checking (typeof, Array.isArray)
     * Support array/object operations (length, includes, indexOf, Object.keys)
     * Return boolean result for branching
   - Set Variable: Set or update workflow variables
     * Resolve variable values from templates
     * Update workflow instance variables JSONB field
     * Variables persist for subsequent steps
   - Delay: Schedule resume after duration (duration acts as timeout)
   - Loop: Execute nested steps iteratively
     * While loop: Repeat until condition is false (when `condition` field provided)
     * ForEach loop: Iterate over array items (when `items` field provided)
     * Track loop context (iteration count, current item, previous outputs)
     * Support break/continue signals
     * Enforce max_iterations safety limit
     * Aggregate outputs from all iterations
   - Sub-workflow: Create new workflow instance (inherit timeout if specified)
5. Handle timeout errors:
   - If timeout exceeded, mark step as failed with timeout error
   - Trigger retry logic if configured
6. Store step output (or timeout error)
7. Extract variables from script output (if `_variables` key present) and update workflow variables
8. Determine next step(s) based on success/failure/timeout
9. Update workflow state (including variables)
10. Continue or complete
```

### Variable Resolution

**For Action Steps and Template Strings:**
Variables are resolved using template syntax: `{{variable.path}}`

- `{{input.key}}` - Input data to workflow instance
- `{{step_id.output.key}}` - Output from a previous step
- `{{env.VAR_NAME}}` - Environment variable
- `{{workflow.variable}}` - Workflow-level variable

**For Condition Steps:**
Conditions use JavaScript-like syntax without template delimiters. Variables are accessed directly:

- `input.key` - Input data to workflow instance
- `step_id.output.key` - Output from a previous step
- `workflow.variable` - Workflow-level variable
- Environment variables are not directly accessible in conditions (use workflow variables instead)

**For Scripts:**
Variables are accessible directly (without `context.` prefix) or via the `context` object:

- `input.key` or `context.input.key` - Input data to workflow instance
- `steps.step_id.output.key` or `context.steps.step_id.output.key` - Output from a previous step
- `workflow.variableName` or `context.workflow.variableName` - Workflow-level variable
- Scripts can also set variables by returning them in a special format (see Script Variable Assignment)

**Variable Assignment:**

Variables can be set in two ways:

1. **Set Variable Step**: Explicitly set variables using the `set_variable` step type
2. **Script Output**: Scripts can set variables by returning a special format

**Script Variable Assignment:**

Scripts can set workflow variables by returning an object with a `_variables` key:

```javascript
// Script sets variables and returns output
return {
  _variables: {
    processedCount: 10,
    lastProcessedId: "abc123",
    status: "completed"
  },
  success: true,
  data: { ... }
};
```

Variables set via script output are merged with existing workflow variables (new values override existing ones).

**Examples:**

```javascript
// Template syntax (for action params, URLs, etc.)
"url": "https://api.example.com/users/{{input.userId}}"
"body": { "data": "{{step1.output.result}}" }
"headers": { "Authorization": "Bearer {{workflow.apiToken}}" }

// JavaScript-like syntax (for conditions)
"condition": "input.userId > 0 && step1.output.status === 'success'"
"condition": "workflow.retryCount < workflow.maxRetries"
"condition": "step1.output.data.length > 0 && workflow.isProcessing === true"

// Script access (direct access recommended)
const apiToken = workflow.apiToken;
const userId = input.userId;
const stepOutput = steps.step1.output;

// Context object access also works
const apiToken2 = context.workflow.apiToken;
const userId2 = context.input.userId;
const stepOutput2 = context.steps.step1.output;
```

---

## 6. Integration with Existing Systems

### Event Integration

Workflows can be triggered by events:

```json
{
  "name": "Trigger Workflow",
  "start_time": "2024-01-01T00:00:00Z",
  "action": {
    "type": "workflow",
    "params": {
      "workflow_id": "workflow-uuid",
      "input": {
        "event_data": "{{metadata}}"
      }
    }
  }
}
```

### Action System Integration

Workflows reuse the existing `ActionsManager` for executing actions:
- Webhook actions
- Websocket actions
- API call actions
- Script actions (JavaScript script execution)
- LLM actions (Large Language Model API calls)
- New action types can be added without workflow changes

**Timeout Handling:**
- Workflow step timeouts are enforced at the workflow execution layer
- For webhook/apicall actions: Timeout is applied via context deadline to HTTP client
- For websocket actions: Timeout can be used to limit connection wait time
- For script actions: Timeout is applied via context deadline to script execution
- For llm actions: Timeout is applied via context deadline to LLM API calls (default: 60s)
- Step-level timeout overrides any default HTTP client timeout
- Timeout errors are caught and handled as step failures, triggering retry logic if configured

**LLM Action Execution:**
- Supports multiple providers: OpenAI, Anthropic, Gemini, OpenRouter
- Provider-specific API client implementations
- Standardized request/response format across providers
- API key management via environment variables or workflow variables
- Token usage tracking in response
- Streaming support (optional)
- Error handling for rate limits, API errors, and timeouts

**Script Execution:**
- Scripts are loaded from the scripts repository by ID or name/version
- Scripts execute in a sandboxed JavaScript runtime (Goja)
- Execution context includes: input data, previous step outputs, workflow variables, console API
- Script return value becomes the step output
- Script errors are caught and step is marked as failed
- Script execution respects step timeout configuration

### Scheduler Integration

Workflows can be scheduled like events:
- One-time workflow execution
- Recurring workflow execution
- Workflow steps can schedule delays

---

## 7. API Design

### Workflow Management

#### Create Workflow
```
POST /workflows
Content-Type: application/json

{
  "name": "My Workflow",
  "description": "Description",
  "definition": { ... },
  "tags": ["tag1", "tag2"]
}

Response: 201 Created
{
  "id": "uuid",
  "name": "My Workflow",
  ...
}
```

#### Get Workflow
```
GET /workflows/{id}

Response: 200 OK
{
  "id": "uuid",
  "name": "My Workflow",
  "definition": { ... },
  ...
}
```

#### List Workflows
```
GET /workflows?tags=tag1,tag2&status=active

Response: 200 OK
{
  "data": [...],
  "pagination": { ... }
}
```

#### Update Workflow
```
PUT /workflows/{id}
Content-Type: application/json

{
  "name": "Updated Name",
  "definition": { ... }
}

Response: 200 OK
```

#### Delete Workflow
```
DELETE /workflows/{id}

Response: 204 No Content
```

### Workflow Instance Management

#### Trigger Workflow
```
POST /workflows/{id}/trigger
Content-Type: application/json

{
  "input": {
    "key": "value"
  }
}

Response: 201 Created
{
  "instance_id": "uuid",
  "status": "pending",
  ...
}
```

#### Get Workflow Instance
```
GET /workflow-instances/{id}

Response: 200 OK
{
  "id": "uuid",
  "workflow_id": "uuid",
  "status": "running",
  "current_step_id": "step2",
  "input_data": { ... },
  "output_data": { ... },
  ...
}
```

#### List Workflow Instances
```
GET /workflow-instances?workflow_id=uuid&status=running

Response: 200 OK
{
  "data": [...],
  "pagination": { ... }
}
```

#### Cancel Workflow Instance
```
POST /workflow-instances/{id}/cancel

Response: 200 OK
{
  "id": "uuid",
  "status": "cancelled",
  ...
}
```

### Step Execution Queries

#### Get Step Executions
```
GET /workflow-instances/{instance_id}/steps

Response: 200 OK
{
  "data": [
    {
      "id": "uuid",
      "step_id": "step1",
      "status": "completed",
      "output_data": { ... },
      ...
    },
    ...
  ]
}
```

---

## Script Management API

### Create Script
```
POST /scripts
Content-Type: application/json

{
  "name": "process-data",
  "description": "Processes input data and returns formatted result",
  "code": "return { success: true, data: input };",
  "tags": ["data-processing", "utility"]
}

Response: 201 Created
{
  "id": "uuid",
  "name": "process-data",
  "version": 1,
  "code": "...",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  ...
}
```

### Get Script
```
GET /scripts/{id}

Response: 200 OK
{
  "id": "uuid",
  "name": "process-data",
  "version": 1,
  "code": "...",
  "status": "active",
  ...
}
```

### Get Script by Name (Latest Version)
```
GET /scripts/by-name/{name}

Response: 200 OK
{
  "id": "uuid",
  "name": "process-data",
  "version": 2,
  "code": "...",
  "status": "active",
  ...
}
```

### Get Script by Name and Version
```
GET /scripts/by-name/{name}/versions/{version}

Response: 200 OK
{
  "id": "uuid",
  "name": "process-data",
  "version": 2,
  "code": "...",
  "status": "active",
  ...
}
```

### List Scripts
```
GET /scripts?tags=tag1,tag2&status=active&name=process

Response: 200 OK
{
  "data": [
    {
      "id": "uuid",
      "name": "process-data",
      "version": 1,
      "status": "active",
      ...
    },
    ...
  ],
  "pagination": { ... }
}
```

### List Script Versions
```
GET /scripts/by-name/{name}/versions

Response: 200 OK
{
  "data": [
    {
      "id": "uuid",
      "name": "process-data",
      "version": 1,
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z",
      ...
    },
    {
      "id": "uuid2",
      "name": "process-data",
      "version": 2,
      "status": "active",
      "created_at": "2024-01-02T00:00:00Z",
      ...
    }
  ]
}
```

### Update Script (Creates New Version)
```
PUT /scripts/{id}
Content-Type: application/json

{
  "code": "return { success: true, data: input, updated: true };",
  "description": "Updated description"
}

Response: 200 OK
{
  "id": "new-uuid",
  "name": "process-data",
  "version": 2,  // New version created
  "code": "...",
  ...
}
```

### Delete Script
```
DELETE /scripts/{id}

Response: 204 No Content
```

### Archive Script
```
POST /scripts/{id}/archive

Response: 200 OK
{
  "id": "uuid",
  "status": "archived",
  ...
}
```

---

## 8. Implementation Plan

### Phase 1: Core Infrastructure
1. Database migrations for workflow tables
2. Database migrations for scripts repository table
3. Workflow models and repositories
4. Script models and repositories
5. Workflow definition validation
6. Basic workflow CRUD API
7. Basic script CRUD API

### Phase 2: Execution Engine
1. Workflow engine core
2. Step executor for actions
3. Timeout handling for step actions
   - Parse timeout duration from step definition
   - Create context with timeout deadline
   - Handle timeout errors and cancellation
   - Integrate with existing HTTP client timeouts
4. State manager
5. Variable resolution system
6. Basic sequential execution
7. Scripts repository and script action support
   - Database schema for scripts repository
   - Script CRUD API endpoints
   - Script versioning system
   - Goja runtime integration (JavaScript execution engine)
   - Script execution context preparation
   - Script error handling and timeout support
8. LLM action support
   - Provider-specific API clients (OpenAI, Anthropic, Gemini, OpenRouter)
   - Standardized request/response format
   - API key management via environment variables
   - Token usage tracking
   - Error handling for rate limits and API errors
   - Streaming support (optional)

### Phase 3: Advanced Features
1. Conditional logic (condition step)
   - JavaScript-like expression evaluator
     * Use a safe expression evaluator library (e.g., `expr` or `govaluate` for Go)
     * Or implement a custom parser for JavaScript-like syntax
     * Support sandboxed execution for security
   - Variable resolution for step outputs, input data, workflow variables
   - Support for comparison, logical, and type-checking operators
   - Array and object operations
   - Type coercion and null/undefined handling
2. Delay step
3. Loop step support
   - While loop implementation (condition-based)
   - ForEach loop implementation (items-based)
   - Loop type detection (condition vs items)
   - Loop context management
   - Break/continue handling
   - Iteration output aggregation
   - Max iterations safety enforcement
4. Parallel execution
5. Error handling and retries
6. Sub-workflow support

### Phase 4: Integration & Polish
1. Event integration (workflow action type)
2. Workflow scheduling
3. Monitoring and observability
4. Performance optimization
5. Documentation

---

## 9. Error Handling & Retries

### Step-Level Retries

Each step can define retry behavior:

```json
{
  "retry": {
    "max_attempts": 3,
    "backoff": "exponential|linear|fixed",
    "initial_delay": "1s",
    "max_delay": "30s"
  }
}
```

### Workflow-Level Error Handling

```json
{
  "error_handler": {
    "step_id": "error_handler_step",
    "action": {
      "type": "webhook",
      "params": {
        "url": "https://webhook.example.com/error"
      }
    }
  }
}
```

### Failure Modes

- **Step Failure**: Retry according to step config, then proceed to `on_failure` step
- **Workflow Failure**: Execute error handler if defined, mark instance as failed
- **Timeout**: Step execution timeout exceeded
  - If a step's `timeout` is exceeded, the step is immediately marked as failed
  - Timeout error is recorded in step execution with error message: "step execution timeout: exceeded {timeout}"
  - Retry logic applies: if retries are configured, the step will be retried up to `max_attempts`
  - Each retry attempt has its own timeout window
  - After all retries are exhausted, `on_failure` step is triggered
  - Timeout applies to action steps (webhook, apicall, websocket)
  - Delay steps use their `duration` as the timeout implicitly
- **Condition Evaluation Error**: Invalid condition expression or runtime error
  - If a condition step's expression cannot be evaluated (syntax error, undefined variable, type error), the step is marked as failed
  - Error message includes details about the evaluation failure
  - Condition evaluation errors do not trigger retries (conditions should be deterministic)
  - Workflow proceeds to `on_false` branch on condition evaluation error
  - Examples of errors: undefined variable access, type mismatch in comparison, invalid operator usage

---

## 10. Performance Considerations

### State Management
- Store workflow state in PostgreSQL for durability
- Cache frequently accessed workflow definitions in Redis
- Use Redis for workflow instance queue

### Execution
- Process workflow instances asynchronously via dispatcher
- Support parallel step execution
- Batch state updates where possible

### Scalability
- Horizontal scaling of workflow dispatchers
- Redis-based coordination for distributed execution
- Database connection pooling

---

## 11. Security Considerations

### Access Control
- Workflows inherit authentication/authorization from existing token system
- Scope-based access control for workflow operations
- Workflow-level tags for multi-tenant isolation

### Data Security
- Sanitize variable resolution to prevent injection
- Validate workflow definitions before execution
- Encrypt sensitive data in workflow state if needed

### Script Security
- **Sandboxed Execution**: Scripts execute in isolated Goja runtime (JavaScript execution engine)
- **No File System Access**: Scripts cannot access file system or external resources
- **No Network Access**: Scripts cannot make network requests (use webhook/apicall actions instead)
- **Timeout Enforcement**: Script execution respects step timeout to prevent infinite loops
- **Resource Limits**: Consider memory and CPU limits for script execution
- **Code Validation**: Validate script syntax before storing in repository
- **Access Control**: Scripts inherit access control from workflow system (tags, scopes)
- **Versioning**: Script versioning allows rollback if security issues are discovered
- **Audit Logging**: Log script execution for security auditing
- **Input Validation**: Validate script input data before execution
- **Output Sanitization**: Sanitize script output before storing as step output

---

## 12. Monitoring & Observability

### Metrics
- Workflow execution count
- Step execution duration
- Failure rates per workflow/step
- Queue depth

### Logging
- Workflow instance lifecycle events
- Step execution details
- Error traces
- Performance metrics

### Tracing
- Trace workflow execution across steps
- Correlate workflow instances with events
- Track sub-workflow execution

---

## 13. Future Enhancements

1. **Visual Workflow Builder**: UI for creating workflows
2. **Workflow Templates**: Pre-built workflow templates
3. **Workflow Versioning**: Version control for workflow definitions
4. **Workflow Testing**: Test workflows with sample data
5. **Workflow Analytics**: Detailed analytics and reporting
6. **Event-Driven Workflows**: Trigger workflows on event patterns
7. **Workflow Scheduling**: Schedule workflows like events
8. **Workflow Notifications**: Notify on workflow completion/failure

---

## 14. Example Use Cases

### 1. API Orchestration
Chain multiple API calls with error handling and conditional logic.

### 2. Data Processing Pipeline
Process data through multiple steps with parallel execution.

### 3. Notification Workflow
Send notifications through multiple channels with retries.

### 4. Approval Workflow
Conditional branching based on approval status.

### 5. Scheduled Reports
Generate and deliver reports on a schedule.

### 6. Data Transformation with Scripts
Use JavaScript scripts to transform data between workflow steps:
- Parse and validate API responses
- Transform data formats
- Calculate derived values
- Filter and aggregate data
- Custom business logic execution

### 7. AI-Powered Workflows with LLM Actions
Use LLM actions to add AI capabilities to workflows:
- Generate summaries and reports from data
- Extract insights and key information
- Natural language processing and understanding
- Content generation (emails, documents, responses)
- Sentiment analysis and classification
- Multi-provider support for flexibility and cost optimization
- Chain multiple LLM calls for complex reasoning

### 8. Agentic AI Workflows with Loops
Use loop steps to create agentic AI workflows that iterate and refine:
- **Iterative Reasoning**: AI agents that think step-by-step until reaching a conclusion
- **Multi-Step Problem Solving**: Break complex problems into iterative sub-problems
- **Refinement Loops**: Iteratively improve outputs until quality threshold is met
- **Batch Processing**: Process arrays of items with AI-powered transformations
- **Conditional Iteration**: Continue processing until specific conditions are met
- **Self-Correction**: Agents that can detect errors and retry with corrections
- **Tool Use**: Agents that can call tools/actions and iterate based on results

**Example Agentic Workflow:**
```json
{
  "id": "agentic_research",
  "name": "Research Agent",
  "steps": [
    {
      "id": "step_research_loop",
      "type": "loop",
      "condition": "step_agent.output.status !== 'complete'",
      "max_iterations": 10,
      "steps": [
        {
          "id": "step_agent",
          "type": "action",
          "action": {
            "type": "llm",
            "params": {
              "provider": "openai",
              "model": "gpt-4",
              "messages": [
                {
                  "role": "system",
                  "content": "You are a research agent. Analyze information and determine if more research is needed."
                },
                {
                  "role": "user",
                  "content": "Research question: {{input.question}}\nCurrent findings: {{loop.previous_output.findings || 'None'}}\nContinue research:"
                }
              ]
            }
          }
        },
        {
          "id": "step_tool_call",
          "type": "action",
          "action": {
            "type": "apicall",
            "params": {
              "method": "GET",
              "url": "{{step_agent.output.tool_url}}"
            }
          },
          "condition": "step_agent.output.needs_tool === true"
        }
      ]
    }
  ]
}
```

---

## 15. Migration Strategy

### Backward Compatibility
- Existing events continue to work unchanged
- Workflows are additive, no breaking changes
- Gradual migration path for users

### Data Migration
- No migration needed for existing data
- New tables created alongside existing ones
- Workflows can reference existing events

---

## Summary

The Workflow System extends Qhronos with powerful orchestration capabilities while maintaining compatibility with existing features. It leverages the existing action system, scheduler, and database infrastructure, providing a seamless extension to the platform.

**Key Features:**
- Multi-step workflows with sequential and parallel execution
- JavaScript-like conditional logic for branching
- Loop step type for iterative execution (while, foreach, for loops)
- Agentic AI support with iterative reasoning and refinement
- Script action type for executing JavaScript scripts from a scripts repository
- LLM action type for calling Large Language Models (OpenAI, Anthropic, Gemini, OpenRouter)
- Script versioning and management system
- **Workflow variables** for state management and data sharing across steps
- **Set Variable step** for explicit variable assignment
- **Script variable assignment** via `_variables` key in script output
- Data flow between steps using template variables
- Error handling and retry strategies
- Sub-workflow support for composition
- Event integration for triggering workflows
- Durable state management with PostgreSQL
- Sandboxed script execution for security
- Multi-provider LLM support with standardized interface

