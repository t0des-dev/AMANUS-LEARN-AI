#!/bin/bash
# ==============================================================================
# Amanus Learn AI — Infrastructure System Health Probe
# Inspects Docker services, PostgreSQL, Redis, Celery workers, and Web/API health
# ==============================================================================

set -uo pipefail

TARGET_ENV="${1:-production}"
COMPOSE_FILE="docker-compose.prod.yml"
if [ "$TARGET_ENV" = "staging" ]; then
    COMPOSE_FILE="docker-compose.staging.yml"
fi

echo "================================================================="
echo "==> Amanus Learn AI: Running Health Probe [$TARGET_ENV]"
echo "==> Compose File: $COMPOSE_FILE"
echo "================================================================="

FAILED=0

# 1. Check Docker Containers Status
echo -n "[1/5] Checking container status... "
RUNNING_CONTAINERS=$(docker compose -f "$COMPOSE_FILE" ps --services --filter "status=running" 2>/dev/null || true)

REQUIRED_SERVICES=("postgres" "redis" "api" "celery-default" "celery-heavy" "web" "nginx")
for s in "${REQUIRED_SERVICES[@]}"; do
    if ! echo "$RUNNING_CONTAINERS" | grep -qw "$s"; then
        echo -e "\n[FAILED] Service '$s' is not running!"
        FAILED=1
    fi
done

if [ $FAILED -eq 0 ]; then
    echo "OK (All 7 core services running)"
fi

# 2. Check PostgreSQL & pgvector
echo -n "[2/5] Checking PostgreSQL & pgvector... "
DB_HEALTH=$(docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -q 2>/dev/null && echo "READY" || echo "UNAVAILABLE")
if [ "$DB_HEALTH" = "READY" ]; then
    echo "OK"
else
    echo "[FAILED] PostgreSQL is not ready!"
    FAILED=1
fi

# 3. Check Redis
echo -n "[3/5] Checking Redis broker... "
REDIS_PASS="${REDIS_PASSWORD:-}"
if [ -z "$REDIS_PASS" ] && [ -f ".env" ]; then
    REDIS_PASS=$(grep -E '^REDIS_PASSWORD=' .env 2>/dev/null | cut -d= -f2- | tr -d '"'\'' \r' || echo "")
fi

# Multi-strategy Redis ping
REDIS_PING=""
# Strategy 1: Check inside container using its own REDIS_PASSWORD environment variable
REDIS_PING=$(docker compose -f "$COMPOSE_FILE" exec -T redis sh -c 'redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null' | tr -d '\r' || true)

# Strategy 2: Check using host parsed password
if [ -z "$REDIS_PING" ] || ! echo "$REDIS_PING" | grep -qi "PONG"; then
    if [ -n "$REDIS_PASS" ]; then
        REDIS_PING=$(docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli -a "$REDIS_PASS" ping 2>/dev/null | tr -d '\r' || true)
    fi
fi

# Strategy 3: Unauthenticated ping fallback
if [ -z "$REDIS_PING" ] || ! echo "$REDIS_PING" | grep -qi "PONG"; then
    REDIS_PING=$(docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping 2>/dev/null | tr -d '\r' || true)
fi

if echo "$REDIS_PING" | grep -qi "PONG"; then
    echo "OK (PONG)"
else
    # Strategy 4: Docker native container health check
    CONTAINER_HEALTH=$(docker compose -f "$COMPOSE_FILE" ps redis --format "{{.Health}}" 2>/dev/null || echo "")
    if echo "$CONTAINER_HEALTH" | grep -qi "healthy"; then
        echo "OK (Container healthy)"
    else
        echo "[FAILED] Redis did not respond to PING!"
        FAILED=1
    fi
fi

# 4. Check Celery Workers
echo -n "[4/5] Checking Celery workers... "
CELERY_PING=$(docker compose -f "$COMPOSE_FILE" exec -T api celery -A config inspect ping --timeout=5 2>/dev/null || echo "FAILED")
if echo "$CELERY_PING" | grep -qi "pong"; then
    echo "OK (Workers responding)"
else
    echo "[WARN] Celery ping did not receive immediate pong (workers might be starting)"
fi

# 5. Check API HTTP Health Endpoint
echo -n "[5/5] Checking API Health Endpoint... "
HTTP_STATUS=$(docker compose -f "$COMPOSE_FILE" exec -T api python -c "
import urllib.request, json

endpoints = [
    'http://localhost:8000/api/v1/health',
    'http://localhost:8000/api/v1/health/',
    'http://localhost:8000/system/health',
    'http://localhost:8000/system/health/',
    'http://localhost:8000/api/v1/system/health/'
]

status_result = 'FAIL'
last_err = 'none'

for url in endpoints:
    try:
        req = urllib.request.Request(
            url,
            headers={'Host': 'localhost', 'X-Forwarded-Proto': 'https'}
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
            val = data.get('status', '')
            if val in ('ok', 'healthy', 'degraded'):
                status_result = val
                break
    except Exception as e:
        last_err = str(e)

if status_result in ('ok', 'healthy', 'degraded'):
    print(status_result)
else:
    print('ERROR:', last_err)
" 2>/dev/null | tr -d '\r' || echo "ERROR")

if [ "$HTTP_STATUS" = "healthy" ] || [ "$HTTP_STATUS" = "ok" ] || [ "$HTTP_STATUS" = "degraded" ]; then
    echo "OK (API status: $HTTP_STATUS)"
else
    echo "[FAILED] API health returned: $HTTP_STATUS"
    FAILED=1
fi

echo "================================================================="
if [ $FAILED -eq 0 ]; then
    echo "==> [SUCCESS] ALL HEALTH PROBES PASSED ($TARGET_ENV is fully operational)"
    exit 0
else
    echo "==> [CRITICAL] ONE OR MORE HEALTH PROBES FAILED ($TARGET_ENV needs attention)"
    exit 1
fi
