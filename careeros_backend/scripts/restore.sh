#!/usr/bin/env bash
set -euo pipefail
BACKUP_FILE=${1:-}
if [[ -z "$BACKUP_FILE" ]]; then
  echo "Usage: $0 <backup-file>"
  exit 1
fi
PG_CONTAINER=${PG_CONTAINER:-postgres}
DB_NAME=${POSTGRES_DB:-careeros}
DB_USER=${POSTGRES_USER:-postgres}

docker compose exec -T "$PG_CONTAINER" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker compose exec -T "$PG_CONTAINER" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"
docker compose exec -T "$PG_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE"

echo "Restore completed"
