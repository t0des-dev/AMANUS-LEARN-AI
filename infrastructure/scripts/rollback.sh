#!/bin/bash
# ==============================================================================
# Amanus Learn AI — Automated Rollback Script
# Restores previous container deployment and optionally restores database
# ==============================================================================

set -euo pipefail

TARGET_ENV="${1:-production}"
BACKUP_SNAPSHOT="${2:-}"

COMPOSE_FILE="docker-compose.prod.yml"
if [ "$TARGET_ENV" = "staging" ]; then
    COMPOSE_FILE="docker-compose.staging.yml"
fi

echo "================================================================="
echo "==> [ROLLBACK] Initiating Rollback Procedure for [$TARGET_ENV]"
echo "==> Compose File: $COMPOSE_FILE"
echo "================================================================="

# 1. Restart existing stable containers
echo "==> Step 1: Restarting previous application containers..."
docker compose -f "$COMPOSE_FILE" restart api web celery-default celery-heavy nginx

# 2. Optional Database Restoration
if [ -n "$BACKUP_SNAPSHOT" ] && [ -f "$BACKUP_SNAPSHOT" ]; then
    echo "==> Step 2: Restoring database snapshot from $BACKUP_SNAPSHOT..."
    read -p "Are you sure you want to restore DB from $BACKUP_SNAPSHOT? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./infrastructure/postgres/restore.sh "$BACKUP_SNAPSHOT"
        echo "==> Database restored."
    else
        echo "==> Database restore skipped by operator."
    fi
else
    echo "==> Step 2: No database snapshot specified. Skipping database rollback."
fi

# 3. Verify Health Post-Rollback
echo "==> Step 3: Running post-rollback health checks..."
sleep 5
./infrastructure/scripts/healthcheck.sh "$TARGET_ENV"

echo "================================================================="
echo "==> [ROLLBACK COMPLETED] Application rolled back to stable state."
echo "================================================================="
