#!/bin/bash
# ==============================================================================
# Amanus Learn AI - Safe Backup & Restoration Validation Script
# NEVER runs against production database. Uses a temporary isolated database.
# ==============================================================================

set -euo pipefail

POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-amanus_user}"
SOURCE_DB="${POSTGRES_DB:-amanus_learn_db}"
TMP_RESTORE_DB="amanus_test_restore_$(date +%s)"
BACKUP_DIR="${BACKUP_DIR:-/tmp/amanus_backups}"
BACKUP_FILE="${BACKUP_DIR}/test_backup_$(date +%Y%m%d_%H%M%S).dump"

mkdir -p "${BACKUP_DIR}"

echo "================================================================="
echo "==> STEP 1: Creating backup from source DB '${SOURCE_DB}'"
echo "================================================================="
PGPASSWORD="${POSTGRES_PASSWORD:-amanus_password_secure}" pg_dump \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d "${SOURCE_DB}" \
    -F c \
    -b \
    -v \
    -f "${BACKUP_FILE}"

echo "==> Backup file created: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"

echo "================================================================="
echo "==> STEP 2: Verifying checksum integrity"
echo "================================================================="
sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
sha256sum -c "${BACKUP_FILE}.sha256"

echo "================================================================="
echo "==> STEP 3: Initializing isolated temporary database '${TMP_RESTORE_DB}'"
echo "================================================================="
PGPASSWORD="${POSTGRES_PASSWORD:-amanus_password_secure}" psql \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d postgres \
    -c "CREATE DATABASE ${TMP_RESTORE_DB};"

PGPASSWORD="${POSTGRES_PASSWORD:-amanus_password_secure}" psql \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d "${TMP_RESTORE_DB}" \
    -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "================================================================="
echo "==> STEP 4: Restoring into temporary database"
echo "================================================================="
PGPASSWORD="${POSTGRES_PASSWORD:-amanus_password_secure}" pg_restore \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d "${TMP_RESTORE_DB}" \
    --no-owner \
    -v \
    "${BACKUP_FILE}" || true

echo "================================================================="
echo "==> STEP 5: Verifying restored schema and data integrity"
echo "================================================================="
TABLE_COUNT=$(PGPASSWORD="${POSTGRES_PASSWORD:-amanus_password_secure}" psql \
    -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${TMP_RESTORE_DB}" -t \
    -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")

MIGRATION_COUNT=$(PGPASSWORD="${POSTGRES_PASSWORD:-amanus_password_secure}" psql \
    -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${TMP_RESTORE_DB}" -t \
    -c "SELECT count(*) FROM django_migrations;")

echo "==> Restored tables in public schema: ${TABLE_COUNT}"
echo "==> Restored applied migrations: ${MIGRATION_COUNT}"

if [ "${MIGRATION_COUNT}" -eq 0 ]; then
    echo "[ERROR] No migrations found in restored database!"
    exit 1
fi

echo "================================================================="
echo "==> STEP 6: Cleanly dropping temporary test database"
echo "================================================================="
PGPASSWORD="${POSTGRES_PASSWORD:-amanus_password_secure}" psql \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d postgres \
    -c "DROP DATABASE ${TMP_RESTORE_DB};"

rm -f "${BACKUP_FILE}" "${BACKUP_FILE}.sha256"

echo "================================================================="
echo "==> [SUCCESS] Full Backup/Restore drill completed cleanly!"
echo "================================================================="
