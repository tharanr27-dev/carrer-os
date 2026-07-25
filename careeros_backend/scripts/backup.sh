#!/usr/bin/env bash
set -euo pipefail
BACKUP_DIR="${BACKUP_DIR:-$(pwd)/backups}"
mkdir -p "$BACKUP_DIR"
TS=$(date +%Y%m%d_%H%M%S)
PG_CONTAINER=${PG_CONTAINER:-postgres}
DB_NAME=${POSTGRES_DB:-careeros}
DB_USER=${POSTGRES_USER:-postgres}

docker compose exec -T "$PG_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_DIR/db_$TS.sql"
docker compose exec -T redis redis-cli BGSAVE >/dev/null
cp -r docker "$BACKUP_DIR/config_$TS"

echo "Backup completed: $BACKUP_DIR"
