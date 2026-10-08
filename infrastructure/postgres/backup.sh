#!/bin/bash
# ==============================================================================
# Amanus Learn AI - Production PostgreSQL Automated Backup Script (Sprint 14)
# ==============================================================================

set -euo pipefail

# Configuration with defaults
BACKUP_DIR="${BACKUP_DIR:-/backups}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-amanus_learn_db}"
POSTGRES_USER="${POSTGRES_USER:-amanus_user}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/amanus_db_${TIMESTAMP}.sql.gz"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"

mkdir -p "${BACKUP_DIR}"

echo "[$(date -Iseconds)] [INFO] Starting PostgreSQL database backup for '${POSTGRES_DB}'..."

# Execute pg_dump with gzip compression
PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_dump \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --format=custom \
    --blobs \
    --verbose \
    | gzip -9 > "${BACKUP_FILE}"

# Generate SHA-256 checksum for backup integrity verification
sha256sum "${BACKUP_FILE}" > "${CHECKSUM_FILE}"

BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "[$(date -Iseconds)] [SUCCESS] Backup created successfully: ${BACKUP_FILE} (${BACKUP_SIZE})"

# Prune old backups older than retention window
echo "[$(date -Iseconds)] [INFO] Pruning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f -name "amanus_db_*.sql.gz*" -mtime +"${RETENTION_DAYS}" -delete

echo "[$(date -Iseconds)] [COMPLETED] Database backup cycle finished."
