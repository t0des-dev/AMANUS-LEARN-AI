#!/bin/bash
# ==============================================================================
# Amanus Learn AI — Production & Staging Zero-Downtime Deployment Orchestrator
# ==============================================================================

set -euo pipefail

TARGET_ENV="${1:-production}"

if [ "$TARGET_ENV" = "staging" ]; then
    COMPOSE_FILE="docker-compose.staging.yml"
    ENV_FILE=".env.staging"
    if [ ! -f "$ENV_FILE" ] && [ -f ".env" ]; then
        ENV_FILE=".env"
    fi
else
    COMPOSE_FILE="docker-compose.prod.yml"
    ENV_FILE=".env"
fi

echo "================================================================="
echo "==> Amanus Learn AI: Initiating Deployment [$TARGET_ENV]"
echo "==> Using Compose File: $COMPOSE_FILE"
echo "==> Using Environment: $ENV_FILE"
echo "================================================================="

# 1. Pre-flight Environment Validation
if [ ! -f "$ENV_FILE" ]; then
    echo "[FATAL] Configuration file '$ENV_FILE' not found!"
    echo "Please copy .env.example or .env.staging.example and configure secrets."
    exit 1
fi

# 2. Pre-deploy Automated Backup
echo "==> [STEP 1/6] Performing pre-deployment PostgreSQL backup..."
BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/tmp/pre_deploy_backup_${TARGET_ENV}_${BACKUP_TIMESTAMP}.sql.gz"

if [ -x "./infrastructure/postgres/backup.sh" ]; then
    BACKUP_DIR="/tmp" BACKUP_FILE="$BACKUP_FILE" ./infrastructure/postgres/backup.sh || {
        echo "[WARN] Backup script failed or database is initializing. Proceeding with caution."
    }
fi

# 3. Build / Pull Container Images
echo "==> [STEP 2/6] Building application container images..."
docker compose -f "$COMPOSE_FILE" build --parallel

# 4. Run Database Migrations in isolated ephemeral container
echo "==> [STEP 3/6] Applying Django database migrations..."
docker compose -f "$COMPOSE_FILE" run --rm api python manage.py migrate --noinput

# 5. Collect Static Assets
echo "==> [STEP 4/6] Collecting static assets..."
docker compose -f "$COMPOSE_FILE" run --rm api python manage.py collectstatic --noinput

# 6. Progressive Zero-Downtime Service Update
echo "==> [STEP 5/6] Updating services with rolling recreation..."
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

# 7. Post-Deployment Verification & Health Probe
echo "==> [STEP 6/6] Validating application health..."
MAX_RETRIES=12
RETRY_DELAY=5
HEALTHY=0

for ((i=1; i<=MAX_RETRIES; i++)); do
    echo -n "==> Probing API health (Attempt $i/$MAX_RETRIES)... "
    if ./infrastructure/scripts/healthcheck.sh "$TARGET_ENV" > /dev/null 2>&1; then
        HEALTHY=1
        echo "HEALTHY!"
        break
    else
        echo "waiting ($RETRY_DELAY s)..."
        sleep $RETRY_DELAY
    fi
done

if [ $HEALTHY -eq 1 ]; then
    echo "================================================================="
    echo "==> [DEPLOY SUCCESS] Amanus Learn AI [$TARGET_ENV] is LIVE and healthy!"
    echo "================================================================="
    exit 0
else
    echo "================================================================="
    echo "==> [DEPLOY FAILED] Health probe failed after deployment!"
    echo "==> Initiating automated rollback to previous container state..."
    echo "================================================================="
    ./infrastructure/scripts/rollback.sh "$TARGET_ENV" "$BACKUP_FILE"
    exit 1
fi
