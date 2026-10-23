# SevaDristi — Production Deployment Guide & Runbook

This guide outlines step-by-step procedures to deploy, operate, and maintain **SevaDristi** in high-availability, low-bandwidth production environments across Telangana MeeSeva / CSC clusters.

---

## 1. Prerequisites

### Infrastructure Requirements
- **Hardware**: Minimum 4 CPU cores, 8 GB RAM, 50 GB SSD storage per node.
- **Operating System**: Ubuntu 22.04 LTS, Debian 12, or RHEL 9.
- **Container Runtimes**:
  - Docker Engine v24.0+ and Docker Compose v2.20+ OR
  - Kubernetes cluster v1.26+ with `kubectl` and NGINX Ingress Controller.
- **Network & Security**:
  - Port 80 / 443 (HTTP/HTTPS) for public ingress.
  - TLS certificates issued via Let's Encrypt or Telangana State Data Center (TSDC) PKI.
  - Egress access to official government scheme feeds if automated sync is enabled.

---

## 2. Environment Configuration

1. Clone repository to deployment server:
   ```bash
   git clone https://github.com/RakeshSaripilly/SevaDristi.git /opt/sevadristi
   cd /opt/sevadristi
   ```

2. Copy `.env.example` to `.env` and configure production secrets:
   ```bash
   cp .env.example .env
   chmod 600 .env
   ```

3. Mandatory Production Settings:
   ```ini
   # Set DEMO_MODE to false to enforce real OCR and fail-closed security
   DEMO_MODE=false

   # 64-character cryptographic entropy for HMAC-SHA256 signing
   SEVADRISTI_QR_SECRET=f3b29c0a1e48d73b6401928374a5b6c7d8e9f0123456789abcdef0123456789a
   # Optional fallback during key rotation
   SEVADRISTI_QR_SECRET_OLD=

   # PostgreSQL async database connection
   DATABASE_URL=postgresql+asyncpg://sevadristi_user:SECURE_DB_PASSWORD@postgres:5432/sevadristi_audit

   # Redis ephemeral cache
   REDIS_URL=redis://redis:6379/0

   LOG_LEVEL=INFO
   ```

---

## 3. Deployment via Docker Compose

1. Build and launch services in detached mode:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
   ```

2. Inspect running container health:
   ```bash
   docker compose ps
   ```

   All 4 services should display `healthy`:
   - `sevadristi-postgres`: PostgreSQL 15 audit ledger
   - `sevadristi-redis`: Ephemeral session cache (7-day TTL)
   - `sevadristi-backend`: FastAPI + Gunicorn workers
   - `sevadristi-frontend`: NGINX serving Vite React PWA

3. Run database migrations:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

---

## 4. Deployment via Kubernetes

1. Create namespace and deploy configuration:
   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/configmap.yaml
   kubectl apply -f k8s/secret.yaml
   kubectl apply -f k8s/pvc.yaml
   ```

2. Deploy database and caching services (if running internal to k8s):
   ```bash
   kubectl apply -f k8s/service.yaml
   ```

3. Deploy backend and frontend application tiers:
   ```bash
   kubectl apply -f k8s/deployment-backend.yaml
   kubectl apply -f k8s/deployment-frontend.yaml
   kubectl apply -f k8s/ingress.yaml
   kubectl apply -f k8s/hpa.yaml
   ```

4. Verify rollout status:
   ```bash
   kubectl rollout status deployment/sevadristi-backend -n sevadristi
   kubectl rollout status deployment/sevadristi-frontend -n sevadristi
   ```

---

## 5. Deployment Verification & Smoke Testing

Run the following curl commands to verify system health:

1. **Detailed Multi-Subsystem Health Check**:
   ```bash
   curl -s http://127.0.0.1:8000/api/health | jq .
   ```
   *Expected Response:*
   ```json
   {
     "status": "healthy",
     "service": "SevaDristi",
     "demo_mode": false,
     "checks": {
       "ocr_available": true,
       "cv2_available": true,
       "qr_secret_configured": true,
       "redis_cache_connected": true,
       "disk_space_ok": true
     }
   }
   ```

2. **Prometheus Metrics Scraping**:
   ```bash
   curl -s http://127.0.0.1:8000/metrics | grep sevadristi_
   ```

3. **Frontend PWA Availability**:
   ```bash
   curl -I http://127.0.0.1:5173/
   ```

---

## 6. Backup and Disaster Recovery

### Automated PostgreSQL Daily Backup
Create a daily cron job on the database host:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/sevadristi"
mkdir -p "${BACKUP_DIR}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
docker compose exec -T postgres pg_dump -U sevadristi_user sevadristi_audit | gzip > "${BACKUP_DIR}/sevadristi_audit_${TIMESTAMP}.sql.gz"

# Retain backups for 30 days
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +30 -delete
```

### Database Restore Procedure
```bash
gunzip < /var/backups/sevadristi/sevadristi_audit_YYYYMMDD_HHMMSS.sql.gz | docker compose exec -T postgres psql -U sevadristi_user -d sevadristi_audit
```

---

## 7. Key Rotation Runbook

To rotate the HMAC-SHA256 signing key without invalidating existing citizen QR tokens in transit:
1. Generate a new 64-character secret.
2. In `.env`:
   - Set `SEVADRISTI_QR_SECRET_OLD` to the current `SEVADRISTI_QR_SECRET`.
   - Set `SEVADRISTI_QR_SECRET` to the new secret.
3. Reload backend instances:
   ```bash
   docker compose restart backend
   ```
4. Tokens signed with the old secret will continue to verify until expiration (24h).
5. After 48 hours, clear `SEVADRISTI_QR_SECRET_OLD`.

---

## 8. Troubleshooting

| Symptom | Probable Cause | Corrective Action |
| :--- | :--- | :--- |
| `/api/verify` returns 503 | Tesseract OCR binary not found | Ensure `tesseract-ocr`, `tesseract-ocr-tel`, and `tesseract-ocr-hin` are installed in the container image. |
| QR signature validation fails | Mismatched secret or tampered token | Verify `SEVADRISTI_QR_SECRET` matches between signing cluster and verification gateway. |
| High memory usage in backend | Excessive concurrent image uploads | Review HPA settings in `k8s/hpa.yaml` and verify Gunicorn worker concurrency (`WEB_CONCURRENCY=4`). |
| Database connection refused | PostgreSQL container initializing | Ensure backend depends on `postgres: condition: service_healthy` in compose. |
| 413 Payload Too Large | Image exceeds 10MB limit | Citizens should use camera capture mode or crop before upload. |
