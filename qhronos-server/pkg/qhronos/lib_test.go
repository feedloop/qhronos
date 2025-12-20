package qhronos

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/feedloop/qhronos-monorepo/qhronos-server/internal/testutils"
	"github.com/stretchr/testify/require"
)

func testConfig(t *testing.T) Config {
	rdb := testutils.TestRedis(t)
	return Config{
		PostgresDSN: os.Getenv("TEST_DATABASE_URL"),
		RedisAddr:   rdb.Options().Addr,
		AuthSecret:  "testsecret",
		HTTPPort:    0,
	}
}

func TestQhronos_EventCRUD(t *testing.T) {
	cfg := testConfig(t)
	qh, err := New(cfg)
	require.NoError(t, err)
	t.Cleanup(func() {
		qh.db.Close()
		qh.redis.Close()
	})

	ctx := context.Background()

	// Create event
	evt := &Event{
		Name:        "Test Event",
		Description: "desc",
		StartTime:   time.Now().Add(time.Hour),
		Webhook:     "https://example.com/webhook",
		Tags:        []string{"test"},
		Metadata:    map[string]interface{}{"foo": "bar"},
	}
	created, err := qh.CreateEvent(ctx, evt)
	require.NoError(t, err)
	require.NotEmpty(t, created.ID)

	// Get event
	got, err := qh.GetEvent(ctx, created.ID)
	require.NoError(t, err)
	require.Equal(t, created.Name, got.Name)

	// List events
	list, err := qh.ListEvents(ctx, []string{"test"})
	require.NoError(t, err)
	require.NotEmpty(t, list)

	// Update event
	got.Description = "updated desc"
	updated, err := qh.UpdateEvent(ctx, got)
	require.NoError(t, err)
	require.Equal(t, "updated desc", updated.Description)

	// Delete event
	err = qh.DeleteEvent(ctx, created.ID)
	require.NoError(t, err)
}

func TestQhronos_CreateToken(t *testing.T) {
	cfg := testConfig(t)
	qh, err := New(cfg)
	require.NoError(t, err)
	t.Cleanup(func() {
		qh.db.Close()
		qh.redis.Close()
	})

	tok, err := qh.CreateToken(context.Background(), &Token{
		Subject:   "user1",
		Access:    "read",
		Scope:     []string{"test"},
		ExpiresAt: time.Now().Add(time.Hour),
	})
	require.NoError(t, err)
	require.NotEmpty(t, tok.Token)
}

func TestQhronos_OccurrenceQueries(t *testing.T) {
	cfg := testConfig(t)
	qh, err := New(cfg)
	require.NoError(t, err)
	t.Cleanup(func() {
		qh.db.Close()
		qh.redis.Close()
	})
	ctx := context.Background()

	// Create event
	evt := &Event{
		Name:        "Occ Event",
		Description: "desc",
		StartTime:   time.Now().Add(time.Hour),
		Webhook:     "https://example.com/webhook",
		Tags:        []string{"occ"},
		Metadata:    map[string]interface{}{"foo": "bar"},
	}
	created, err := qh.CreateEvent(ctx, evt)
	require.NoError(t, err)

	// List occurrences by tags (should be empty)
	occs, err := qh.ListOccurrencesByTags(ctx, []string{"occ"})
	require.NoError(t, err)
	require.Empty(t, occs)

	// List occurrences by event (should be empty)
	occs, err = qh.ListOccurrencesByEvent(ctx, created.ID)
	require.NoError(t, err)
	require.Empty(t, occs)

	// Get occurrence (should be not found)
	occ, err := qh.GetOccurrence(ctx, "00000000-0000-0000-0000-000000000000")
	require.NoError(t, err)
	require.Nil(t, occ)
}

func TestQhronos_Migrate(t *testing.T) {
	cfg := testConfig(t)
	qh, err := New(cfg)
	require.NoError(t, err)
	t.Cleanup(func() {
		qh.db.Close()
		qh.redis.Close()
	})
	err = qh.Migrate(context.Background())
	require.NoError(t, err)
}

func TestQhronos_ErrorCases(t *testing.T) {
	cfg := testConfig(t)
	qh, err := New(cfg)
	require.NoError(t, err)
	t.Cleanup(func() {
		qh.db.Close()
		qh.redis.Close()
	})
	ctx := context.Background()

	t.Run("Get non-existent event", func(t *testing.T) {
		got, err := qh.GetEvent(ctx, "00000000-0000-0000-0000-000000000000")
		require.NoError(t, err)
		require.Nil(t, got)
	})
	t.Run("Delete non-existent event", func(t *testing.T) {
		err := qh.DeleteEvent(ctx, "00000000-0000-0000-0000-000000000000")
		require.NoError(t, err)
	})
	t.Run("Create event missing required fields", func(t *testing.T) {
		_, err := qh.CreateEvent(ctx, &Event{})
		require.Error(t, err)
	})
}

func TestQhronos_TokenExpiry(t *testing.T) {
	cfg := testConfig(t)
	qh, err := New(cfg)
	require.NoError(t, err)
	t.Cleanup(func() {
		qh.db.Close()
		qh.redis.Close()
	})
	expired := time.Now().Add(-time.Hour)
	tok, err := qh.CreateToken(context.Background(), &Token{
		Subject:   "expired",
		Access:    "read",
		Scope:     []string{"test"},
		ExpiresAt: expired,
	})
	require.NoError(t, err)
	require.NotEmpty(t, tok.Token)
	require.WithinDuration(t, expired, tok.ExpiresAt, time.Second)
}
