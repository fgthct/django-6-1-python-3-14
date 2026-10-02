#!/usr/bin/env bash
# Uso: scripts/ripristina.sh db-AAAAMMGG-hhmmss.dump media-AAAAMMGG-hhmmss.tar
# Sostituisce il contenuto del database e dei file con quelli del backup.
set -euo pipefail

DUMP="$1"
MEDIA="$2"
[ -f "$DUMP" ] && [ -f "$MEDIA" ] || { echo "File di backup non trovati" >&2; exit 1; }

docker compose up -d db
docker compose stop web proxy

docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' < "$DUMP"
docker compose run --rm --no-deps -T --user root web sh -c 'rm -rf /dati/media && tar -C /dati -xf - && chown -R vault /dati/media' < "$MEDIA"

docker compose up -d --wait
echo "Ripristino completato."
