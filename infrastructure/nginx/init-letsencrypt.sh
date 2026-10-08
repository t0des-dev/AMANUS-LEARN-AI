#!/bin/bash
# ==============================================================================
# Amanus Learn AI — Let's Encrypt / Certbot Automated SSL Initialization
# ==============================================================================

set -euo pipefail

DOMAINS=("${DOMAINS:-app.amanuslearn.com}")
EMAIL="${EMAIL:-admin@amanuslearn.com}"
STAGING_MODE="${STAGING_MODE:-0}" # Set to 1 for Let's Encrypt staging test CA
DATA_PATH="./infrastructure/nginx/ssl"

if [ -d "$DATA_PATH/live/${DOMAINS[0]}" ]; then
    echo "==> Certificate directory $DATA_PATH/live/${DOMAINS[0]} already exists."
    read -p "Overwrite existing certificates? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

mkdir -p "$DATA_PATH/live/${DOMAINS[0]}"

# Step 1: Generate temporary self-signed certificate so Nginx starts without SSL failure
echo "==> Step 1: Creating temporary self-signed certificate for Nginx startup..."
openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "$DATA_PATH/live/privkey.pem" \
    -out "$DATA_PATH/live/fullchain.pem" \
    -subj "/CN=localhost" 2>/dev/null || true

# Step 2: Start Nginx to serve ACME challenge
echo "==> Step 2: Starting Nginx..."
docker compose -f docker-compose.prod.yml up -d nginx

# Step 3: Request genuine Let's Encrypt certificates
echo "==> Step 3: Requesting genuine certificates from Let's Encrypt..."
DOMAIN_ARGS=""
for d in "${DOMAINS[@]}"; do
    DOMAIN_ARGS="$DOMAIN_ARGS -d $d"
done

STAGING_ARG=""
if [ "$STAGING_MODE" != "0" ]; then
    STAGING_ARG="--staging"
fi

docker compose -f docker-compose.prod.yml run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $STAGING_ARG \
    $DOMAIN_ARGS \
    --email $EMAIL \
    --rsa-key-size 4096 \
    --agree-tos \
    --force-renewal \
    --non-interactive" certbot

# Step 4: Reload Nginx with new genuine certificates
echo "==> Step 4: Reloading Nginx with production TLS certificates..."
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload

echo "================================================================="
echo "==> [SUCCESS] SSL Certificates installed and Nginx reloaded!"
echo "================================================================="
