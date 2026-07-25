# CareerOS AI Infrastructure

## Deployment architecture

- FastAPI service runs behind Nginx and exposes health endpoints at `/health`, `/health/live`, and `/health/ready`.
- PostgreSQL, Redis, Celery, Qdrant, Prometheus, Grafana, Loki, Promtail, and Jaeger are provided as containerized services.
- Observability is centralized through Prometheus, Loki, and OpenTelemetry, with Grafana dashboards for operational visibility.

## Docker architecture

- Development stack: `docker-compose.dev.yml`
- Production stack: `docker-compose.prod.yml`
- Default stack: `docker-compose.yml`

## Container communication

- The API container connects to PostgreSQL and Redis over the Docker network.
- Celery workers consume tasks from Redis and write results back through Redis.
- Nginx proxies requests to the API service with websocket-friendly headers.

## Monitoring and logging

- Prometheus scrapes metrics from the API and other services.
- Loki and Promtail collect container logs.
- Grafana visualizes system health and service metrics.

## Backup and recovery

- Run `bash scripts/backup.sh` to create database and configuration backups.
- Run `bash scripts/restore.sh <backup-file>` to restore a database backup.

## CI/CD

- GitHub Actions workflow: `.github/workflows/ci-cd.yml`
