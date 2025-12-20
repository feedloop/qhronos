# Qhronos Python SDK

Official Python SDK for [Qhronos](https://github.com/feedloop/qhronos-monorepo) - Event Scheduling and Workflow Orchestration Platform.

## Installation

```bash
pip install qhronos
# or
poetry add qhronos
# or
uv add qhronos
```

## Quick Start

### Synchronous Client

```python
from datetime import datetime, timedelta
from qhronos import QhronosClient, EventCreateParams

client = QhronosClient(
    base_url="https://api.qhronos.io",
    token="your-api-token",
)

# Create an event
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

print(f"Created event: {event.id}")
```

### Asynchronous Client

```python
import asyncio
from datetime import datetime, timedelta
from qhronos import AsyncQhronosClient, EventCreateParams

async def main():
    async with AsyncQhronosClient(
        base_url="https://api.qhronos.io",
        token="your-api-token",
    ) as client:
        event = await client.events.create(
            EventCreateParams(
                name="Daily Report",
                start_time=datetime.now() + timedelta(hours=1),
            )
        )
        print(f"Created event: {event.id}")

asyncio.run(main())
```

## Features

- **Sync and Async clients** for flexible usage patterns
- **Full type hints** with Pydantic models
- **All resources covered**: Events, Jobs, Workflows, Scripts, Integrations
- **Error handling** with typed exception classes
- **Context manager support** for proper resource cleanup

## API Reference

### Client Configuration

```python
from qhronos import QhronosClient, AsyncQhronosClient

# Synchronous
client = QhronosClient(
    base_url="https://api.qhronos.io",  # Required
    token="your-api-token",              # Required
    timeout=30.0,                        # Optional (default: 30.0)
    headers={"X-Custom": "header"},      # Optional
    debug=False,                         # Optional
)

# Asynchronous
async_client = AsyncQhronosClient(
    base_url="https://api.qhronos.io",
    token="your-api-token",
)
```

### Events

```python
from qhronos import EventCreateParams, EventUpdateParams

# Create
event = client.events.create(
    EventCreateParams(
        name="My Event",
        start_time=datetime.now(),
        action={"type": "webhook", "params": {"url": "..."}},
    )
)

# Get
event = client.events.get("event-id")

# Update
updated = client.events.update(
    "event-id",
    EventUpdateParams(name="New Name")
)

# Delete
client.events.delete("event-id")

# List
events = client.events.list(tags=["important"], limit=20)

# Pause/Resume
client.events.pause("event-id")
client.events.resume("event-id")

# Trigger immediately
result = client.events.trigger("event-id")
```

### Jobs

```python
from qhronos import JobStatus, JobType

# Get
job = client.jobs.get("job-id")

# List
jobs = client.jobs.list(
    status=JobStatus.COMPLETED,
    type=JobType.WORKFLOW,
    limit=50,
)

# Cancel
client.jobs.cancel("job-id")

# Retry
client.jobs.retry("job-id")

# Get child jobs
children = client.jobs.children("job-id")
```

### Workflows

```python
from qhronos import WorkflowCreateParams

# Create
workflow = client.workflows.create(
    WorkflowCreateParams(
        name="Data Pipeline",
        definition={
            "steps": [
                {
                    "id": "fetch",
                    "type": "action",
                    "action": {"type": "apicall", "params": {"url": "..."}},
                    "next": "process",
                },
                {
                    "id": "process",
                    "type": "action",
                    "action": {"type": "script", "params": {"script_id": "..."}},
                },
            ]
        },
    )
)

# Execute
job = client.workflows.execute("workflow-id", params={"userId": "123"})

# Get workflow jobs
jobs = client.workflows.jobs("workflow-id")
```

### Scripts

```python
from qhronos import ScriptCreateParams

# Create
script = client.scripts.create(
    ScriptCreateParams(
        name="Data Transformer",
        code="""
            const data = input.data;
            return { processed: data.length };
        """,
    )
)

# Execute
job = client.scripts.execute("script-id", params={"data": [1, 2, 3]})
```

### Integrations

```python
from qhronos import IntegrationCreateParams, IntegrationType, IntegrationProvider

# Create LLM integration
llm = client.integrations.create(
    IntegrationCreateParams(
        name="OpenAI GPT-4",
        type=IntegrationType.LLM,
        provider=IntegrationProvider.OPENAI,
        config={"api_key": "...", "model": "gpt-4"},
    )
)

# Create notification integration
slack = client.integrations.create(
    IntegrationCreateParams(
        name="Slack Alerts",
        type=IntegrationType.NOTIFICATION,
        provider=IntegrationProvider.SLACK,
        config={"webhook_url": "..."},
    )
)

# Test integration
result = client.integrations.test("integration-id")
```

## Error Handling

```python
from qhronos import QhronosAPIError, QhronosNetworkError, QhronosTimeoutError

try:
    event = client.events.get("non-existent")
except QhronosAPIError as e:
    print(f"API Error: {e.message} (status={e.status_code}, code={e.code})")
except QhronosTimeoutError:
    print("Request timed out")
except QhronosNetworkError as e:
    print(f"Network Error: {e.message}")
```

## Context Manager

```python
# Synchronous
with QhronosClient(base_url="...", token="...") as client:
    events = client.events.list()

# Asynchronous
async with AsyncQhronosClient(base_url="...", token="...") as client:
    events = await client.events.list()
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src

# Run type checking
mypy src
```

## License

MIT

