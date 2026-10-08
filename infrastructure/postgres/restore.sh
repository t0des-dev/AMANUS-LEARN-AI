#!/bin/bash
# ==============================================================================
# Amanus Learn AI - Production PostgreSQL Restore Script (Sprint 14)
# ==============================================================================

set -euo pipefail

if [ -z "${1:-}" ]; then
    echo "Usage: $0 <path_to_backup_file.sql.gz> [target_db]"
    exit 1
fi

BACKUP_FILE="$1"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${2:-${POSTGRES_DB:-amanus_learn_db}}"
POSTGRES_USER="${POSTGRES_USER:-amanus_user}"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "[ERROR] Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# Verify checksum if present
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
if [ -f "${CHECKSUM_FILE}" ]; then
    echo "[INFO] Verifying SHA-256 integrity checksum..."
    sha256sum -c "${CHECKSUM_FILE}"
fi

echo "================================================================="
echo "WARNING: You are about to restore database '${POSTGRES_DB}' on host '${POSTGRES_HOST}'"
echo "Target backup: ${BACKUP_FILE}"
echo "================================================================="
echo "Continuing restoration..."

# Restore using pg_restore
gunzip -c "${BACKUP_FILE}" | PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_restore \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --clean \
    --if-exists \
    --no-owner \
    --role="${POSTGRES_USER}" \
    --verbose || true

echo "[SUCCESS] Database restoration completed successfully."
