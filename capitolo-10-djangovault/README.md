# DjangoVault (Capitolo 10, Progetto 7 opzionale)

Django 6.1, Python 3.14, uv, PostgreSQL + pgvector, HTMX.

## Avvio

    uv sync
    # database: utente e database "vault" (password "vault"), estensione vector
    # variabili: DB_PORT (default 5432), DB_NAME
    uv run python manage.py migrate
    EMBEDDING_BACKEND=finto uv run python manage.py crea_demo
    EMBEDDING_BACKEND=finto uv run python manage.py runserver

Utenti demo: marta, luca, giulia, paolo (password "password").

## Test (67)

    uv run pytest

`EMBEDDING_BACKEND=finto` usa un embedder finto (nessun download); `fastembed` usa il modello vero.
