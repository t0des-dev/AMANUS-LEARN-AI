#!/bin/bash
# ==============================================================================
# Amanus Learn AI — Secret Rotation & Git History Purge Helper
#
# Rotates Django SECRET_KEY, DB password (prints instructions), and reissues
# self-signed TLS certs. Optionally purges tracked secrets from git history.
#
# Usage:
#   ./rotate_secrets.sh                  # rotate local secrets + regenerate self-signed certs
#   ./rotate_secrets.sh --purge-history  # ALSO purge *.pem / *.key from git history (DESTRUCTIVE)
#
# NOTE: For production, prefer certbot + a real secret manager over this script.
#       This script is a safety net for local/staging and for cleaning git.
# ==============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PURGE_HISTORY=0
if [[ "${1:-}" == "--purge-history" ]]; then
    PURGE_HISTORY=1
fi

echo "================================================================="
echo "==> Amanus Learn AI: Secret Rotation Helper"
echo "================================================================="

# 1. Generate a new Django SECRET_KEY
echo "[1/4] Generating new Django SECRET_KEY..."
NEW_SECRET_KEY="$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null \
    || openssl rand -base64 50 | tr -d '\n' | tr '+/' '-_')"
if [[ -z "$NEW_SECRET_KEY" ]]; then
    echo "[FAILED] Could not generate a secret key."
    exit 1
fi
echo "      New SECRET_KEY generated (set it in your environment / secret manager):"
echo "      SECRET_KEY=$NEW_SECRET_KEY"
echo ""

# 2. Print DB password rotation instructions
echo "[2/4] Database password rotation checklist:"
echo "      a) ALTER USER amanus_user WITH PASSWORD '<new_password>';   # on Postgres"
echo "      b) Update DATABASE_URL in .env / .env.production"
echo "      c) Rotate the same value in Docker secrets / CI variables"
echo "      d) Restart api + celery services"
echo ""

# 3. Regenerate self-signed certs (dev/staging only — production uses certbot)
SSL_DIR="infrastructure/nginx/ssl/live"
echo "[3/4] Regenerating self-signed TLS certificate (dev/staging only)..."
mkdir -p "$SSL_DIR"
if command -v openssl >/dev/null 2>&1; then
    openssl req -x509 -nodes -newkey rsa:2048 -days 90 \
        -keyout "$SSL_DIR/privkey.pem" \
        -out "$SSL_DIR/fullchain.pem" \
        -subj "/CN=localhost" 2>/dev/null
    chmod 600 "$SSL_DIR/privkey.pem"
    echo "      Wrote $SSL_DIR/{privkey,fullchain}.pem (90-day self-signed)"
else
    echo "      [SKIP] openssl not found. For production run: certbot renew"
fi
echo ""

# 4. Optional: purge tracked secrets from git history
if [[ "$PURGE_HISTORY" -eq 1 ]]; then
    echo "[4/4] Purging tracked secrets from git history (DESTRUCTIVE)..."
    if command -v git-filter-repo >/dev/null 2>&1; then
        git filter-repo --invert-paths \
            --path-glob '*.pem' \
            --path-glob '*.key' \
            --force
        echo "      Done. You must now force-push every remote branch:"
        echo "        git push --force --all origin"
        echo "        git push --force --tags origin"
    elif command -v bfg >/dev/null 2>&1; then
        bfg --delete-glob '*.pem' --delete-glob '*.key' .
        echo "      Done. Run: git reflog expire --expire=now --all && git gc --prune=now --aggressive"
    else
        echo "      [SKIP] Neither git-filter-repo nor bfg found."
        echo "      Install: pip install git-filter-repo   (or download BFG jar)"
        echo "      Historical PEMs remain until purged — ROTATE the certs regardless."
    fi
else
    echo "[4/4] Skipping history purge (pass --purge-history to enable)."
fi

echo ""
echo "================================================================="
echo "==> Rotation complete. Checklist:"
echo "    [ ] Update SECRET_KEY in env / secret manager"
echo "    [ ] Update DATABASE_URL password everywhere"
echo "    [ ] Reissue production certs (certbot renew)"
echo "    [ ] Purge git history if secrets were ever committed"
echo "    [ ] Force-push after history rewrite + coordinate with team"
echo "================================================================="
