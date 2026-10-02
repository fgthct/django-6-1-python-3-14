#!/usr/bin/env bash
# Uso: scripts/backup.sh [cartella]   (da eseguire nella cartella del progetto, con lo stack acceso)
set -euo pipefail

DEST="${1:-backup}"
SIGLA="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$DEST"

# Prima il database, poi i file: se nel frattempo arriva un caricamento, il backup contiene un file in più
# senza la sua riga (un orfano, innocuo), mai una riga senza il suo file (che sarebbe un documento rotto).
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$DEST/db-$SIGLA.dump"
docker compose exec -T web tar -C /dati -cf - media > "$DEST/media-$SIGLA.tar"

# Un backup che non si riesce nemmeno a elencare è già inutile: lo si scopre adesso, non il giorno del disastro.
docker compose exec -T db pg_restore --list < "$DEST/db-$SIGLA.dump" > /dev/null
tar -tf "$DEST/media-$SIGLA.tar" > /dev/null

echo "Backup completo: $DEST/db-$SIGLA.dump  $DEST/media-$SIGLA.tar"
