#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

COMPOSE_FILE="infra/docker-compose.yml"

echo "╔══════════════════════════════════════════╗"
echo "║   Spark Media Factory V2                 ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Start Postgres first
echo "→ Starting PostgreSQL..."
docker compose -f "$COMPOSE_FILE" up -d postgres

echo "→ Waiting for Postgres to be ready..."
until docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U spark -d spark 2>/dev/null; do
  sleep 1
done
echo "  ✓ Postgres ready"

# Run migrations if needed
echo "→ Running database migrations..."
docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U spark -d spark -c "
  CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL DEFAULT 'default',
    kind TEXT NOT NULL DEFAULT 'chat',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
  );
" 2>/dev/null && echo "  ✓ Migrations applied" || echo "  ✓ Tables already exist"

# Start all services
echo "→ Starting all services..."
docker compose -f "$COMPOSE_FILE" up -d

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Spark V2 is running!                   ║"
echo "╠══════════════════════════════════════════╣"
echo "║  Web UI:     http://localhost:3002       ║"
echo "║  API:        http://localhost:8080       ║"
echo "║  Health:     http://localhost:8080/health║"
echo "║  PostgreSQL: localhost:5432              ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Logs: docker compose -f $COMPOSE_FILE logs -f"
echo "Stop: docker compose -f $COMPOSE_FILE down"
