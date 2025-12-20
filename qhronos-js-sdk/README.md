# Qhronos JavaScript/TypeScript SDK

Official JavaScript/TypeScript SDK for [Qhronos](https://github.com/feedloop/qhronos-monorepo) - Event Scheduling and Workflow Orchestration Platform.

## Installation

```bash
npm install @qhronos/sdk
# or
yarn add @qhronos/sdk
# or
pnpm add @qhronos/sdk
```

## Quick Start

```typescript
import { QhronosClient } from '@qhronos/sdk';

const client = new QhronosClient({
  baseUrl: 'https://api.qhronos.io',
  token: 'your-api-token',
});

// Create an event
const event = await client.events.create({
  name: 'Daily Report',
  start_time: new Date(Date.now() + 3600000).toISOString(),
  action: {
    type: 'webhook',
    params: { url: 'https://example.com/webhook' }
  },
  schedule: { frequency: 'daily' }
});

console.log('Created event:', event.id);
```

## Features

- **Full TypeScript support** with comprehensive type definitions
- **Promise-based API** for async/await usage
- **All resources covered**: Events, Jobs, Workflows, Scripts, Integrations
- **Error handling** with typed error classes
- **Request customization** with timeouts, headers, and idempotency keys

## API Reference

### Client Configuration

```typescript
const client = new QhronosClient({
  baseUrl: 'https://api.qhronos.io',  // Required
  token: 'your-api-token',             // Required
  timeout: 30000,                       // Optional (default: 30000ms)
  headers: { 'X-Custom': 'header' },   // Optional
  debug: false,                         // Optional
});
```

### Events

```typescript
// Create
const event = await client.events.create({
  name: 'My Event',
  start_time: new Date().toISOString(),
  action: { type: 'webhook', params: { url: '...' } },
});

// Get
const event = await client.events.get('event-id');

// Update
const updated = await client.events.update('event-id', { name: 'New Name' });

// Delete
await client.events.delete('event-id');

// List
const events = await client.events.list({ tags: ['important'], limit: 20 });

// Pause/Resume
await client.events.pause('event-id');
await client.events.resume('event-id');

// Trigger immediately
const { job_id } = await client.events.trigger('event-id');
```

### Jobs

```typescript
// Get
const job = await client.jobs.get('job-id');

// List
const jobs = await client.jobs.list({ 
  status: 'completed',
  type: 'workflow',
  limit: 50 
});

// Cancel
await client.jobs.cancel('job-id');

// Retry
await client.jobs.retry('job-id');

// Get child jobs
const children = await client.jobs.children('job-id');
```

### Workflows

```typescript
// Create
const workflow = await client.workflows.create({
  name: 'Data Pipeline',
  definition: {
    steps: [
      {
        id: 'fetch',
        type: 'action',
        action: { type: 'apicall', params: { url: '...' } },
        next: 'process'
      },
      {
        id: 'process',
        type: 'action',
        action: { type: 'script', params: { script_id: '...' } }
      }
    ]
  }
});

// Execute
const job = await client.workflows.execute('workflow-id', {
  params: { userId: '123' }
});

// Get workflow jobs
const jobs = await client.workflows.jobs('workflow-id');
```

### Scripts

```typescript
// Create
const script = await client.scripts.create({
  name: 'Data Transformer',
  code: `
    const data = input.data;
    return { processed: data.length };
  `
});

// Execute
const job = await client.scripts.execute('script-id', {
  params: { data: [1, 2, 3] }
});
```

### Integrations

```typescript
// Create LLM integration
const llm = await client.integrations.create({
  name: 'OpenAI GPT-4',
  type: 'llm',
  provider: 'openai',
  config: { api_key: '...', model: 'gpt-4' }
});

// Create notification integration
const slack = await client.integrations.create({
  name: 'Slack Alerts',
  type: 'notification',
  provider: 'slack',
  config: { webhook_url: '...' }
});

// Test integration
const result = await client.integrations.test('integration-id');
```

## Error Handling

```typescript
import { QhronosApiError, QhronosNetworkError } from '@qhronos/sdk';

try {
  await client.events.get('non-existent');
} catch (error) {
  if (error instanceof QhronosApiError) {
    console.error('API Error:', error.message, error.status, error.code);
  } else if (error instanceof QhronosNetworkError) {
    console.error('Network Error:', error.message, error.type);
  }
}
```

## Request Options

```typescript
// Per-request options
const event = await client.events.create(
  { name: 'Event', start_time: new Date().toISOString() },
  {
    timeout: 5000,
    headers: { 'X-Request-ID': 'abc123' },
    idempotencyKey: 'unique-key',
  }
);
```

## License

MIT

