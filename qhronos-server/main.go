package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"github.com/feedloop/qhronos-monorepo/qhronos-server/pkg/qhronos"
	"github.com/spf13/pflag"
)

func main() {
	// CLI flags
	migrate := pflag.BoolP("migrate", "m", false, "Run database migrations and exit")
	version := pflag.BoolP("version", "v", false, "Print version and exit")
	port := pflag.IntP("port", "p", 8080, "HTTP server listen port")
	masterToken := pflag.String("master-token", "", "Override master token from config")

	pflag.Parse()

	if *version {
		fmt.Println("qhronosd version 1.0.0")
		os.Exit(0)
	}

	// Load config (simple YAML or env parsing, or just use flags for now)
	cfg := qhronos.Config{
		PostgresDSN: os.Getenv("QHRONOS_POSTGRES_DSN"),
		RedisAddr:   os.Getenv("QHRONOS_REDIS_ADDR"),
		AuthSecret:  os.Getenv("QHRONOS_AUTH_SECRET"),
		HTTPPort:    *port,
	}
	if *masterToken != "" {
		cfg.AuthSecret = *masterToken
	}
	// Optionally, parse from config file if needed

	qh, err := qhronos.New(cfg)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to initialize Qhronos: %v\n", err)
		os.Exit(1)
	}

	if *migrate {
		err = qh.Migrate(context.Background())
		if err != nil {
			fmt.Fprintf(os.Stderr, "Migration failed: %v\n", err)
			os.Exit(1)
		}
		fmt.Println("Migrations applied successfully.")
		os.Exit(0)
	}

	// Start HTTP server
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-quit
		fmt.Println("Shutting down server...")
		cancel()
	}()

	fmt.Printf("Starting Qhronos server on port %d...\n", cfg.HTTPPort)
	if err := qh.StartHTTPServer(ctx); err != nil && err.Error() != "http: Server closed" {
		fmt.Fprintf(os.Stderr, "Server error: %v\n", err)
		os.Exit(1)
	}
}
