package qhronos

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
	"github.com/redis/go-redis/v9"
	"go.uber.org/zap"

	"github.com/feedloop/qhronos-monorepo/qhronos-server/internal/api"
	"github.com/feedloop/qhronos-monorepo/qhronos-server/internal/database"
	"github.com/feedloop/qhronos-monorepo/qhronos-server/internal/handlers"
	"github.com/feedloop/qhronos-monorepo/qhronos-server/internal/middleware"
	"github.com/feedloop/qhronos-monorepo/qhronos-server/internal/models"
	"github.com/feedloop/qhronos-monorepo/qhronos-server/internal/repository"
	"github.com/feedloop/qhronos-monorepo/qhronos-server/internal/services"
	"github.com/gin-gonic/gin"

	"github.com/feedloop/qhronos-monorepo/qhronos-server/migrations"
	"github.com/golang-migrate/migrate/v4"
	"github.com/golang-migrate/migrate/v4/database/postgres"
	"github.com/golang-migrate/migrate/v4/source/iofs"
)

// Config holds all configuration options for Qhronos (DB, Redis, etc.)
type Config struct {
	PostgresDSN string
	RedisAddr   string
	AuthSecret  string
	HTTPPort    int
	// ... other fields as needed
}

// Qhronos is the main struct for interacting with the library.
type Qhronos struct {
	db             *sqlx.DB
	redis          *redis.Client
	logger         *zap.Logger
	eventRepo      *repository.EventRepository
	occurrenceRepo *repository.OccurrenceRepository
	tokenService   *services.TokenService
	redisPrefix    string
	httpServer     *http.Server
	masterToken    string
}

// New creates a new Qhronos instance with the given config.
func New(cfg Config) (*Qhronos, error) {
	// Parse PostgresDSN (expected format: postgres://user:pass@host:port/dbname?sslmode=disable)
	pgConfig, err := parsePostgresDSN(cfg.PostgresDSN)
	if err != nil {
		return nil, fmt.Errorf("invalid PostgresDSN: %w", err)
	}
	db, err := database.Connect(*pgConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Postgres: %w", err)
	}

	// Parse RedisAddr (expected format: host:port)
	redisOpts, err := parseRedisAddr(cfg.RedisAddr)
	if err != nil {
		return nil, fmt.Errorf("invalid RedisAddr: %w", err)
	}
	redisClient := redis.NewClient(redisOpts)

	// Logger (use zap for now)
	logger := zap.NewNop()

	// Namespace/prefix for Redis keys (optional, can be made configurable)
	redisPrefix := "qhronos:"

	// Repositories
	eventRepo := repository.NewEventRepository(db, logger, redisClient, redisPrefix)
	occurrenceRepo := repository.NewOccurrenceRepository(db, logger)

	// Token service
	tokenService := services.NewTokenService(cfg.AuthSecret, cfg.AuthSecret)

	return &Qhronos{
		db:             db,
		redis:          redisClient,
		logger:         logger,
		eventRepo:      eventRepo,
		occurrenceRepo: occurrenceRepo,
		tokenService:   tokenService,
		redisPrefix:    redisPrefix,
		httpServer:     nil,
		masterToken:    cfg.AuthSecret,
	}, nil
}

// parsePostgresDSN parses a DSN string into a database.Config
func parsePostgresDSN(dsn string) (*database.Config, error) {
	// Very basic parser for DSN, expects format: postgres://user:pass@host:port/dbname?sslmode=disable
	if !strings.HasPrefix(dsn, "postgres://") {
		return nil, fmt.Errorf("unsupported DSN format")
	}
	dsn = strings.TrimPrefix(dsn, "postgres://")
	userPassHostDb := strings.SplitN(dsn, "@", 2)
	if len(userPassHostDb) != 2 {
		return nil, fmt.Errorf("invalid DSN")
	}
	userPass := strings.SplitN(userPassHostDb[0], ":", 2)
	if len(userPass) != 2 {
		return nil, fmt.Errorf("invalid user:pass in DSN")
	}
	hostDb := userPassHostDb[1]
	hostPortDb := strings.SplitN(hostDb, "/", 2)
	if len(hostPortDb) != 2 {
		return nil, fmt.Errorf("invalid host/db in DSN")
	}
	hostPort := strings.SplitN(hostPortDb[0], ":", 2)
	if len(hostPort) != 2 {
		return nil, fmt.Errorf("invalid host:port in DSN")
	}
	params := strings.SplitN(hostPortDb[1], "?", 2)
	sslmode := "disable"
	if len(params) == 2 && strings.HasPrefix(params[1], "sslmode=") {
		sslmode = strings.TrimPrefix(params[1], "sslmode=")
	}
	return &database.Config{
		Host:     hostPort[0],
		Port:     mustAtoi(hostPort[1]),
		User:     userPass[0],
		Password: userPass[1],
		DBName:   params[0],
		SSLMode:  sslmode,
	}, nil
}

func mustAtoi(s string) int {
	n, _ := fmt.Sscanf(s, "%d", new(int))
	if n == 1 {
		return n
	}
	return 5432 // default
}

// parseRedisAddr parses host:port into redis.Options
func parseRedisAddr(addr string) (*redis.Options, error) {
	parts := strings.Split(addr, ":")
	if len(parts) != 2 {
		return nil, fmt.Errorf("invalid RedisAddr format")
	}
	return &redis.Options{
		Addr: addr,
		DB:   0,
	}, nil
}

// StartHTTPServer starts the HTTP API server (optional).
func (q *Qhronos) StartHTTPServer(ctx context.Context) error {
	// Set up Gin engine
	gin.SetMode(gin.ReleaseMode)
	router := gin.New()

	// Basic logging middleware (can be extended)
	router.Use(gin.Logger())
	router.Use(gin.Recovery())

	// Handlers
	eventHandler := handlers.NewEventHandler(q.eventRepo, nil) // expander is nil for now
	occurrenceHandler := handlers.NewOccurrenceHandler(q.eventRepo, q.occurrenceRepo)
	tokenHandler := handlers.NewTokenHandler(q.tokenService)
	rateLimiter := middleware.NewRateLimiter(q.redis)

	// Setup routes
	api.SetupRoutes(router, eventHandler, occurrenceHandler, tokenHandler, rateLimiter, q.masterToken)

	// HTTP server
	srv := &http.Server{
		Addr:    ":8080", // TODO: make configurable
		Handler: router,
	}
	q.httpServer = srv

	// Graceful shutdown on context cancel
	shutdownCh := make(chan os.Signal, 1)
	signal.Notify(shutdownCh, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-ctx.Done()
		_ = srv.Shutdown(context.Background())
	}()

	go func() {
		<-shutdownCh
		_ = srv.Shutdown(context.Background())
	}()

	return srv.ListenAndServe()
}

// StopHTTPServer gracefully stops the HTTP server.
func (q *Qhronos) StopHTTPServer(ctx context.Context) error {
	if q.httpServer != nil {
		return q.httpServer.Shutdown(ctx)
	}
	return nil
}

// Event represents a scheduled event.
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

// Schedule represents recurrence rules.
type Schedule struct {
	Frequency string // e.g., "daily", "weekly"
	Interval  int
	// ... other recurrence fields
}

// Occurrence represents a single scheduled execution of an event.
type Occurrence struct {
	ID      string
	EventID string
	Status  string
	RunAt   time.Time
	// ... other fields
}

// Token represents an authentication token.
type Token struct {
	Token     string
	Type      string
	Subject   string
	Access    string
	Scope     []string
	ExpiresAt time.Time
}

// Event CRUD
func (q *Qhronos) CreateEvent(ctx context.Context, event *Event) (*Event, error) {
	// Map to internal model
	internalEvent := &models.Event{
		ID:          uuid.New(),
		Name:        event.Name,
		Description: event.Description,
		StartTime:   event.StartTime,
		Webhook:     event.Webhook,
		Metadata:    nil,
		Schedule:    nil,
		Tags:        event.Tags,
		Status:      models.EventStatusActive,
	}
	if event.Metadata != nil {
		metaBytes, err := json.Marshal(event.Metadata)
		if err != nil {
			return nil, err
		}
		internalEvent.Metadata = metaBytes
	}
	if event.Schedule != nil {
		internalEvent.Schedule = &models.ScheduleConfig{
			Frequency: event.Schedule.Frequency,
			Interval:  event.Schedule.Interval,
		}
	}
	if err := q.eventRepo.Create(ctx, internalEvent); err != nil {
		return nil, err
	}
	return &Event{
		ID:          internalEvent.ID.String(),
		Name:        internalEvent.Name,
		Description: internalEvent.Description,
		StartTime:   internalEvent.StartTime,
		Webhook:     internalEvent.Webhook,
		Metadata:    event.Metadata,
		Schedule:    event.Schedule,
		Tags:        internalEvent.Tags,
	}, nil
}

func (q *Qhronos) GetEvent(ctx context.Context, id string) (*Event, error) {
	internalEvent, err := q.eventRepo.GetEvent(ctx, id)
	if err != nil || internalEvent == nil {
		return nil, err
	}
	var meta map[string]interface{}
	if internalEvent.Metadata != nil {
		_ = json.Unmarshal(internalEvent.Metadata, &meta)
	}
	var sched *Schedule
	if internalEvent.Schedule != nil {
		sched = &Schedule{
			Frequency: internalEvent.Schedule.Frequency,
			Interval:  internalEvent.Schedule.Interval,
		}
	}
	return &Event{
		ID:          internalEvent.ID.String(),
		Name:        internalEvent.Name,
		Description: internalEvent.Description,
		StartTime:   internalEvent.StartTime,
		Webhook:     internalEvent.Webhook,
		Metadata:    meta,
		Schedule:    sched,
		Tags:        internalEvent.Tags,
	}, nil
}

func (q *Qhronos) ListEvents(ctx context.Context, tags []string) ([]*Event, error) {
	internalEvents, err := q.eventRepo.ListByTags(ctx, tags)
	if err != nil {
		return nil, err
	}
	var result []*Event
	for _, internalEvent := range internalEvents {
		var meta map[string]interface{}
		if internalEvent.Metadata != nil {
			_ = json.Unmarshal(internalEvent.Metadata, &meta)
		}
		var sched *Schedule
		if internalEvent.Schedule != nil {
			sched = &Schedule{
				Frequency: internalEvent.Schedule.Frequency,
				Interval:  internalEvent.Schedule.Interval,
			}
		}
		result = append(result, &Event{
			ID:          internalEvent.ID.String(),
			Name:        internalEvent.Name,
			Description: internalEvent.Description,
			StartTime:   internalEvent.StartTime,
			Webhook:     internalEvent.Webhook,
			Metadata:    meta,
			Schedule:    sched,
			Tags:        internalEvent.Tags,
		})
	}
	return result, nil
}

func (q *Qhronos) UpdateEvent(ctx context.Context, event *Event) (*Event, error) {
	id, err := uuid.Parse(event.ID)
	if err != nil {
		return nil, err
	}
	internalEvent, err := q.eventRepo.GetByID(ctx, id)
	if err != nil || internalEvent == nil {
		return nil, err
	}
	// Update fields
	internalEvent.Name = event.Name
	internalEvent.Description = event.Description
	internalEvent.StartTime = event.StartTime
	internalEvent.Webhook = event.Webhook
	if event.Metadata != nil {
		metaBytes, err := json.Marshal(event.Metadata)
		if err != nil {
			return nil, err
		}
		internalEvent.Metadata = metaBytes
	}
	if event.Schedule != nil {
		internalEvent.Schedule = &models.ScheduleConfig{
			Frequency: event.Schedule.Frequency,
			Interval:  event.Schedule.Interval,
		}
	}
	internalEvent.Tags = event.Tags
	if err := q.eventRepo.Update(ctx, internalEvent); err != nil {
		return nil, err
	}
	return q.GetEvent(ctx, event.ID)
}

func (q *Qhronos) DeleteEvent(ctx context.Context, id string) error {
	uid, err := uuid.Parse(id)
	if err != nil {
		return err
	}
	return q.eventRepo.Delete(ctx, uid)
}

// Occurrence queries
func (q *Qhronos) ListOccurrencesByTags(ctx context.Context, tags []string) ([]*Occurrence, error) {
	filter := models.OccurrenceFilter{
		Tags:  tags,
		Page:  1,
		Limit: 100, // default limit, can be made configurable
	}
	internalOccs, _, err := q.occurrenceRepo.ListByTags(ctx, filter)
	if err != nil {
		return nil, err
	}
	var result []*Occurrence
	for _, occ := range internalOccs {
		result = append(result, &Occurrence{
			ID:      occ.OccurrenceID.String(),
			EventID: occ.EventID.String(),
			Status:  string(occ.Status),
			RunAt:   occ.ScheduledAt,
			// Add more fields as needed
		})
	}
	return result, nil
}

func (q *Qhronos) ListOccurrencesByEvent(ctx context.Context, eventID string) ([]*Occurrence, error) {
	uid, err := uuid.Parse(eventID)
	if err != nil {
		return nil, err
	}
	internalOccs, err := q.occurrenceRepo.ListByEventID(ctx, uid)
	if err != nil {
		return nil, err
	}
	var result []*Occurrence
	for _, occ := range internalOccs {
		result = append(result, &Occurrence{
			ID:      occ.OccurrenceID.String(),
			EventID: occ.EventID.String(),
			Status:  string(occ.Status),
			RunAt:   occ.ScheduledAt,
			// Add more fields as needed
		})
	}
	return result, nil
}

func (q *Qhronos) GetOccurrence(ctx context.Context, id string) (*Occurrence, error) {
	uid, err := uuid.Parse(id)
	if err != nil {
		return nil, err
	}
	occ, err := q.occurrenceRepo.GetLatestByOccurrenceID(ctx, uid)
	if err != nil || occ == nil {
		return nil, err
	}
	return &Occurrence{
		ID:      occ.OccurrenceID.String(),
		EventID: occ.EventID.String(),
		Status:  string(occ.Status),
		RunAt:   occ.ScheduledAt,
		// Add more fields as needed
	}, nil
}

// Token management
func (q *Qhronos) CreateToken(ctx context.Context, t *Token) (*Token, error) {
	// Map to internal CreateTokenRequest
	req := &models.CreateTokenRequest{
		Type:      models.TokenTypeJWT,
		Sub:       t.Subject,
		Access:    models.AccessLevel(t.Access),
		Scope:     t.Scope,
		ExpiresAt: t.ExpiresAt,
	}
	tokenStr, err := q.tokenService.CreateJWTToken(req)
	if err != nil {
		return nil, err
	}
	return &Token{
		Token:     tokenStr,
		Type:      "jwt",
		Subject:   t.Subject,
		Access:    t.Access,
		Scope:     t.Scope,
		ExpiresAt: t.ExpiresAt,
	}, nil
}

// (Optional) Migration
func (q *Qhronos) Migrate(ctx context.Context) error {
	db := q.db.DB
	d, err := iofs.New(migrations.FS, "migrations")
	if err != nil {
		return err
	}
	driver, err := postgres.WithInstance(db, &postgres.Config{})
	if err != nil {
		return err
	}
	m, err := migrate.NewWithInstance("iofs", d, "postgres", driver)
	if err != nil {
		return err
	}
	err = m.Up()
	if err != nil && err != migrate.ErrNoChange {
		return err
	}
	return nil
}
