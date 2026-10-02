# DjangoVault (Capitolo 11: dal portatile al server)

Django 6.1, Python 3.14, uv, PostgreSQL 18 + pgvector, HTMX, gunicorn, WhiteNoise, Docker Compose, Caddy.

## Sviluppo

Serve un PostgreSQL 18 con l'estensione `vector` e un utente `vault` (password `vault`) con permesso di creare database.
In sviluppo si dice `DEBUG=1`: senza, l'applicazione si considera in produzione e non parte.

    uv sync
    export DEBUG=1 EMBEDDING_BACKEND=finto
    uv run python manage.py migrate
    uv run python manage.py crea_demo
    uv run python manage.py runserver

Variabili utili: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

## Test e controlli (118 test)

    uv run pytest --cov
    uv run ruff check . && uv run ruff format --check .
    DEBUG=1 uv run python manage.py makemigrations --check --dry-run

## Produzione con Docker Compose

    cp .env.example .env        # poi modifica i valori
    docker compose up -d --build --wait
    curl -fsk https://localhost/pronto/

Backup e ripristino:

    scripts/backup.sh backup
    scripts/verifica-backup.sh backup/db-AAAAMMGG-hhmmss.dump
    scripts/ripristina.sh backup/db-AAAAMMGG-hhmmss.dump backup/media-AAAAMMGG-hhmmss.tar

Il workflow di integrazione continua è in `.github/workflows/ci.yml`.
