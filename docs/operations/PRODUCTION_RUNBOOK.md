# Amanus Learn AI — Production & Staging Operations Runbook

**Version:** 1.0 (Phase 16)  
**Target Environments:** Staging (`staging.amanuslearn.com`), Production (`app.amanuslearn.com`)  
**Audience:** DevOps Engineers, Platform Administrators, On-Call Team

---

## 1. Architecture Topology

```
Internet (HTTPS 443 / HTTP 80)
           │
           ▼
    ┌──────────────┐
    │ Nginx Reverse│  <-- SSL / TLS Termination, Security Headers,
    │    Proxy     │      Rate Limiting, SSE Unbuffered Streaming
    └──────┬───────┘
           │
    ┌──────┴──────────────────────┬────────────────────────┐
    ▼                             ▼                        ▼
┌──────────────┐          ┌──────────────┐         ┌──────────────┐
│ Next.js Web  │          │  Django API  │         │ Certbot SSL  │
│  (Port 3000) │          │ (Gunicorn:8k)│         │ Auto-Renewal │
└──────────────┘          └──────┬───────┘         └──────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           ▼                     ▼                     ▼
    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
    │  PostgreSQL  │      │   Redis 7    │      │  MinIO / S3  │
    │  16+pgvector │      │ Cache/Broker │      │ Document S3  │
    └──────────────┘      └──────┬───────┘      └──────────────┘
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
    ┌──────────────────────────┐             ┌──────────────────────────┐
    │ Celery Default Worker    │             │ Celery Heavy Worker      │
    │ (Notifications, Reports) │             │ (OCR, RAG, Audio, PPTX)  │
    └──────────────────────────┘             └──────────────────────────┘
```

---

## 2. Server Sizing & Prerequisites

### Minimum Hardware Recommendations
| Environment | vCPU | RAM | Disk (NVMe/SSD) | Network |
| :--- | :---: | :---: | :---: | :---: |
| **Staging** | 2 | 4 GB | 40 GB | 100 Mbps |
| **Production** | 4 | 8 GB | 100 GB | 1 Gbps |

### Host OS & Software
- Ubuntu 22.04 LTS or 24.04 LTS
- Docker CE >= 25.0
- Docker Compose Plugin >= 2.24
- Git, curl, openssl

---

## 3. Initial Server Setup

```bash
# 1. Update OS and install Docker
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 2. Clone Repository
git clone https://github.com/organization/amanus-learn-ai.git /opt/amanus-learn-ai
cd /opt/amanus-learn-ai

# 3. Configure Secrets
cp .env.example .env
# Edit .env with secure production values (SECRET_KEY, POSTGRES_PASSWORD, REDIS_PASSWORD, etc.)
chmod 600 .env
```

---

## 4. SSL / TLS Setup (Let's Encrypt)

```bash
# Execute automated Let's Encrypt initialization
DOMAINS="app.amanuslearn.com" EMAIL="admin@amanuslearn.com" ./infrastructure/nginx/init-letsencrypt.sh
```

The script will:
1. Generate temporary bootstrap certificates.
2. Spin up Nginx with ACME HTTP challenge listener.
3. Request genuine certificates from Let's Encrypt.
4. Reload Nginx with production TLS 1.2/1.3 parameters.
5. The `certbot` container continuously renews certificates every 12 hours.

---

## 5. Deployment Procedures

### Automated Zero-Downtime Deployment
```bash
# Deploy to Staging
./infrastructure/scripts/deploy.sh staging

# Deploy to Production
./infrastructure/scripts/deploy.sh production
```

**Deployment Lifecycle:**
1. Validates environment configuration file (`.env` or `.env.staging`).
2. Creates an automated database snapshot in `/tmp/pre_deploy_backup_*.sql.gz`.
3. Builds container images in parallel.
4. Runs database migrations in an isolated container (`migrate --noinput`).
5. Collects static assets (`collectstatic --noinput`).
6. Replaces containers with rolling recreation (`docker compose up -d`).
7. Runs automated health probes (`/api/v1/system/health/`).
8. If health checks fail, automatically rolls back to the previous stable state!

### Manual Rollback
```bash
# Roll back containers and optionally restore database
./infrastructure/scripts/rollback.sh production /tmp/pre_deploy_backup_production_TIMESTAMP.sql.gz
```

---

## 6. Backup & Disaster Recovery

### Automated Daily Backup (Cron)
Add to `/etc/cron.d/amanus-backup`:
```cron
# Run daily database backup at 02:00 UTC
0 2 * * * root cd /opt/amanus-learn-ai && ./infrastructure/postgres/backup.sh >> /var/log/amanus-backup.log 2>&1
```

### Safe Non-Destructive Restore Drill
```bash
# Runs full restore against an isolated temporary database without touching production
./infrastructure/postgres/validate_backup_restore.sh
```

---

## 7. Monitoring & Observability

### Health Checks
```bash
# Run comprehensive infrastructure probe
./infrastructure/scripts/healthcheck.sh production
```

### Launching Prometheus & Grafana
```bash
# Start Prometheus, Grafana, and Exporters
docker compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d
```
- **Prometheus:** `http://localhost:9090` (Scrapes API health, PostgreSQL, Redis, Celery).
- **Grafana:** `http://localhost:3001` (Pre-configured Prometheus datasource).

---

## 8. Troubleshooting Guide

| Symptom | Probable Cause | Action |
| :--- | :--- | :--- |
| **502 Bad Gateway** | API container restarting or not healthy | Check `docker compose logs api`. Verify `DATABASE_URL` connectivity. |
| **SSE stream stalls** | Nginx buffering or proxy timeout | Ensure client connects to `/api/v1/chat/sessions/.../messages` routed through dedicated unbuffered Nginx block. |
| **Celery jobs delayed** | Heavy queue saturation | Check worker logs: `docker compose logs celery-heavy`. Scale worker: `docker compose up -d --scale celery-heavy=2`. |
| **Database connection refused** | PostgreSQL initializing or memory limit | Check `docker compose logs postgres`. Ensure `pgvector` container is healthy. |
