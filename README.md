# Qhronos

<p align="center">
  <strong>Event Scheduling and Workflow Orchestration Platform</strong>
</p>

<p align="center">
  A powerful, scalable platform for scheduling events, executing workflows, and orchestrating complex automation tasks.
</p>

---

## Overview

Qhronos is an enterprise-grade scheduling and workflow orchestration platform that enables you to:

- **Schedule Events**: Create one-time or recurring events with flexible scheduling options
- **Execute Workflows**: Build multi-step workflows with conditional logic, loops, and sub-workflows
- **Run Scripts**: Execute JavaScript code with access to external APIs, databases, and LLMs
- **Integrate Services**: Connect to LLMs, notification channels, and databases through a unified integration system
- **Monitor Jobs**: Track all executions with comprehensive logging and metrics

## Repository Structure

This is a monorepo containing:

| Package | Description | Status |
|---------|-------------|--------|
| [qhronos-server](./qhronos-server) | Go backend server | Production |
| [qhronos-js-sdk](./qhronos-js-sdk) | JavaScript/TypeScript SDK | Development |
| [qhronos-python-sdk](./qhronos-python-sdk) | Python SDK (sync & async) | Development |
| [design](./design) | Design documents and specifications | Active |

## Quick Start

### Server

```bash
cd qhronos-server

# Configure
cp config.example.yml config.yml
# Edit config.yml with your settings

# Run with Docker
docker-compose up -d

# Or build and run directly
make build
./bin/qhronosd
```

### JavaScript/TypeScript SDK

```bash
npm install @qhronos/sdk
```

```typescript
import { QhronosClient } from '@qhronos/sdk';

const client = new QhronosClient({
  baseUrl: 'https://api.qhronos.io',
  token: 'your-api-token',
});

// Create a scheduled event
const event = await client.events.create({
  name: 'Daily Report',
  start_time: new Date(Date.now() + 3600000).toISOString(),
  action: {
    type: 'webhook',
    params: { url: 'https://example.com/webhook' }
  },
  schedule: { frequency: 'daily' }
});

// Execute a workflow
const job = await client.workflows.execute('workflow-id', {
  params: { userId: '123' }
});
```

### Python SDK

```bash
pip install qhronos
```

```python
from datetime import datetime, timedelta
from qhronos import QhronosClient, EventCreateParams

client = QhronosClient(
    base_url="https://api.qhronos.io",
    token="your-api-token",
)

# Create a scheduled event
event = client.events.create(
    EventCreateParams(
        name="Daily Report",
        start_time=datetime.now() + timedelta(hours=1),
        action={
    "type": "webhook",
            "params": {"url": "https://example.com/webhook"}
  },
    )
)

# Execute a workflow
job = client.workflows.execute("workflow-id", params={"userId": "123"})
```

## Features

### Event Scheduling
- One-time and recurring events
- Flexible recurrence rules (daily, weekly, monthly, yearly)
- Timezone support
- Event pausing and resumption

### Workflow System
- Multi-step workflows with dependencies
- Conditional branching
- Loops (while and foreach)
- Sub-workflow support
- Variable management
- Error handling and retries

### Script Execution
- JavaScript runtime (Goja)
- Built-in modules (crypto, uuid, validator, jsonpath)
- HTTP fetch support
- Database access (MySQL, PostgreSQL)
- LLM integration
- File system operations

### Integrations
- **LLM Providers**: OpenAI, Anthropic, Gemini, OpenRouter
- **Notifications**: Amazon SES, Twilio, Slack, Discord, Telegram
- **Databases**: MySQL, PostgreSQL

### Action Types
- **Webhook**: Send HTTP requests to external endpoints
- **WebSocket**: Real-time notifications via WebSocket
- **API Call**: Make HTTP requests and capture responses
- **Script**: Execute JavaScript code
- **Workflow**: Trigger workflow execution
- **Integration**: Use configured integrations

### Observability
- Prometheus metrics
- Structured logging
- Distributed tracing (OpenTelemetry)
- Comprehensive job history

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
│                    (REST + WebSocket)                            │
├─────────────────────────────────────────────────────────────────┤
│                      Core Services                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │  Event   │  │ Workflow │  │  Script  │  │ Integration  │    │
│  │ Manager  │  │  Engine  │  │  Runner  │  │   Manager    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                      Scheduler                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │ Expander │  │Dispatcher│  │  Action  │  │   Cleanup    │    │
│  │          │  │          │  │ Executor │  │   Manager    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                      Data Layer                                  │
│  ┌──────────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   PostgreSQL     │  │    Redis     │  │  Object Storage │   │
│  │  (Events, Jobs)  │  │  (Schedules) │  │     (Files)     │   │
│  └──────────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Documentation

- [API Documentation](./qhronos-server/docs/api.md)
- [Embedding Guide](./qhronos-server/docs/embedding.md)
- [Design Document](./design/design.md)
- [Workflow Design](./design/workflow-design.md)
- [Script Design](./design/script-design.md)
- [Client Design](./design/client-design.md)
- [Implementation Plan](./plans/plan.md)

## Development

### Prerequisites

- Go 1.21+
- Node.js 18+
- Python 3.9+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Setup

```bash
# Clone the repository
git clone https://github.com/feedloop/qhronos-monorepo.git
cd qhronos

# Start infrastructure
docker-compose -f qhronos-server/docker-compose.yml up -d postgres redis

# Run the server
cd qhronos-server
make run

# Install JS SDK dependencies
cd ../qhronos-js-sdk
npm install

# Install Python SDK dependencies
cd ../qhronos-python-sdk
pip install -e ".[dev]"
```

### Testing

```bash
# Server tests
cd qhronos-server
make test

# JS SDK tests
cd qhronos-js-sdk
npm test

# Python SDK tests
cd qhronos-python-sdk
pytest
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](./qhronos-server/CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](./qhronos-server/LICENSE) for details.

---

<p align="center">
  Built with ❤️ by the Qhronos Team
</p>
