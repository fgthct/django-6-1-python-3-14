#!/usr/bin/env bash
# Uso: scripts/verifica-backup.sh db-AAAAMMGG-hhmmss.dump
# Ripristina il backup in un database temporaneo e confronta i conteggi con quello vivo.
set -euo pipefail

DUMP="$1"
docker compose exec -T db sh -c 'dropdb -U "$POSTGRES_USER" --if-exists prova_ripristino && createdb -U "$POSTGRES_USER" prova_ripristino'
docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d prova_ripristino --no-owner' < "$DUMP"

CONTA="SELECT 'documenti ' || count(*) FROM documenti_documento UNION ALL SELECT 'versioni ' || count(*) FROM documenti_versione UNION ALL SELECT 'passaggi ' || count(*) FROM documenti_chunk;"
echo "--- nel backup";
docker compose exec -T db sh -c "psql -U \"\$POSTGRES_USER\" -d prova_ripristino -At -c \"$CONTA\""
echo "--- nel database vivo";
docker compose exec -T db sh -c "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -At -c \"$CONTA\""
docker compose exec -T db sh -c 'dropdb -U "$POSTGRES_USER" prova_ripristino'
