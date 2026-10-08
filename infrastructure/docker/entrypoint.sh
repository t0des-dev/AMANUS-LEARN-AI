#!/bin/sh
set -e

echo "==> Amanus Learn AI: Checking environment..."

# Wait for PostgreSQL
PG_HOST="${POSTGRES_HOST:-postgres}"
PG_PORT="${POSTGRES_PORT:-5432}"

echo "==> Waiting for PostgreSQL on $PG_HOST:$PG_PORT..."
count=0
while ! nc -z "$PG_HOST" "$PG_PORT"; do
    sleep 1
    count=$((count + 1))
    if [ "$count" -ge 30 ]; then
        echo "==> Warning: PostgreSQL wait timed out after 30s. Continuing..."
        break
    fi
done
echo "==> PostgreSQL is ready or timeout reached."

# Run database migrations
echo "==> Running Django database migrations..."
python manage.py migrate --noinput || true

exec "$@"
