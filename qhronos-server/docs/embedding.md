# Qhronos Go Library

Qhronos is a developer-first scheduling and notification platform.
This package allows you to embed Qhronos directly into your Go applications, providing programmatic access to all major features: event scheduling, occurrence tracking, token management, and (optionally) running the HTTP API server.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Core Types](#core-types)
- [Main Functions](#main-functions)
  - [Initialization](#initialization)
  - [Event Management](#event-management)
  - [Occurrence Management](#occurrence-management)
  - [Token Management](#token-management)
  - [HTTP Server (Optional)](#http-server-optional)
  - [Database Migration (Optional)](#database-migration-optional)
- [Example: Embedding Qhronos in Your App](#example-embedding-qhronos-in-your-app)
- [Error Handling](#error-handling)
- [FAQ](#faq)
- [Notes](#notes)
- [Contributing](#contributing)
- [License](#license)

---

## Installation

```sh
go get github.com/feedloop/qhronos-monorepo/qhronos-server/pkg/qhronos
```

---

## Quick Start

```go
import (
    "context"
    "time"
    "github.com/feedloop/qhronos-monorepo/qhronos-server/pkg/qhronos"
)

func main() {
    cfg := qhronos.Config{
        // Fill in database, Redis, and other config fields
    }
    qh, err := qhronos.New(cfg)
    if err != nil {
        panic(err)
    }

    // Create an event
    event := &qhronos.Event{
        Name:        "My Event",
        Description: "A test event",
        StartTime:   time.Now().Add(1 * time.Hour),
        Webhook:     "https://example.com/webhook",
        Tags:        []string{"api"},
    }
    created, err := qh.CreateEvent(context.Background(), event)
    if err != nil {
        panic(err)
    }

    // (Optional) Start HTTP API server
    go qh.StartHTTPServer(context.Background())
}
```

---

## Configuration

The `Config` struct contains all necessary configuration for Qhronos, including database, Redis, and authentication settings.

```go
type Config struct {
    PostgresDSN string
    RedisAddr   string
    AuthSecret  string
    HTTPPort    int
    // ... other fields as needed
}
```

You can construct a `Config` manually or load it from your application's configuration system.

---

## Core Types

- **Qhronos**: Main struct for interacting with the library.
- **Event**: Represents a scheduled event.
- **Occurrence**: Represents a scheduled execution of an event.
- **Token**: Represents an authentication token.
- **Schedule**: Recurrence rules for events.

```go
type Qhronos struct { /* ... */ }

type Event struct {
    ID          string
    Name        string
    Description string
    StartTime   time.Time
    Schedule    *Schedule // nil for one-time
    Webhook     string
    Metadata    map[string]interface{}
    Tags        []string
    // ... other fields
}

type Schedule struct {
    Frequency string // e.g., "daily", "weekly"
    Interval  int
    // ... other recurrence fields
}

type Occurrence struct {
    ID        string
    EventID   string
    Status    string
    RunAt     time.Time
    // ... other fields
}

type Token struct {
    Token     string
    Type      string
    Subject   string
    Access    string
    Scope     []string
    ExpiresAt time.Time
}
```

---

## Main Functions

### Initialization

```go
qh, err := qhronos.New(cfg)
```
Creates a new Qhronos instance with the given configuration.

---

### Event Management

```go
event, err := qh.CreateEvent(ctx, &qhronos.Event{...})
event, err := qh.GetEvent(ctx, eventID)
events, err := qh.ListEvents(ctx, tags)
event, err := qh.UpdateEvent(ctx, &qhronos.Event{...})
err = qh.DeleteEvent(ctx, eventID)
```

- **CreateEvent**: Schedules a new event (one-time or recurring).
- **GetEvent**: Retrieves an event by ID.
- **ListEvents**: Lists events, optionally filtered by tags.
- **UpdateEvent**: Updates an existing event.
- **DeleteEvent**: Deletes an event by ID.

---

### Occurrence Management

```go
occurrences, err := qh.ListOccurrencesByTags(ctx, tags)
occurrences, err := qh.ListOccurrencesByEvent(ctx, eventID)
occurrence, err := qh.GetOccurrence(ctx, occurrenceID)
```

- **ListOccurrencesByTags**: Lists occurrences filtered by tags.
- **ListOccurrencesByEvent**: Lists occurrences for a specific event.
- **GetOccurrence**: Retrieves a specific occurrence by ID.

---

### Token Management

```go
token, err := qh.CreateToken(ctx, &qhronos.Token{...})
```

- **CreateToken**: Creates a new authentication token (JWT or master token).

---

### HTTP Server (Optional)

```go
err := qh.StartHTTPServer(ctx)
err := qh.StopHTTPServer(ctx)
```

- **StartHTTPServer**: Starts the HTTP API server (optional).
- **StopHTTPServer**: Gracefully stops the HTTP server.

---

### Database Migration (Optional)

```go
err := qh.Migrate(ctx)
```

- **Migrate**: Applies all pending database migrations.

---

## Example: Embedding Qhronos in Your App

```go
package main

import (
    "context"
    "time"
    "github.com/feedloop/qhronos-monorepo/qhronos-server/pkg/qhronos"
)

func main() {
    cfg := qhronos.Config{
        PostgresDSN: "postgres://user:pass@localhost:5432/qhronos",
        RedisAddr:   "localhost:6379",
        AuthSecret:  "supersecret",
        HTTPPort:    8080,
    }
    qh, err := qhronos.New(cfg)
    if err != nil {
        panic(err)
    }

    // Create an event
    event := &qhronos.Event{
        Name:      "My Event",
        StartTime: time.Now().Add(10 * time.Minute),
        Webhook:   "https://example.com/webhook",
    }
    created, err := qh.CreateEvent(context.Background(), event)
    if err != nil {
        panic(err)
    }

    // Start HTTP server (optional)
    go qh.StartHTTPServer(context.Background())

    // ... your app logic ...
}
```

---

## Error Handling

All methods return Go `error` values.
Errors may be standard Go errors or custom error types (e.g., for not found, validation, etc.).

---

## FAQ

**Q: Can I use Qhronos without running the HTTP server?**
A: Yes! All core features are available via Go APIs. The HTTP server is optional.

**Q: Is the standalone binary still available?**
A: Yes. The CLI/server binary is still available and now uses the same library internally.

**Q: How do I run database migrations?**
A: Use the `Migrate` method or the CLI.

**Q: Can I extend Qhronos with custom actions?**
A: Not directly via the library API yet, but the codebase is designed for extensibility.

---

## Notes

- Qhronos uses PostgreSQL and Redis for storage and scheduling.
- All API methods are context-aware for cancellation and timeouts.
- The library is thread-safe and can be used in concurrent applications.

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## License

Qhronos is licensed under the MIT License. See [LICENSE](../LICENSE) for details.

--- 