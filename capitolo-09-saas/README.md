# Assistenza (Progetto 6)

Un helpdesk multi-tenant: un sottodominio per cliente, API con Django Ninja,
dashboard con HTMX, CSP completa. Codice del Capitolo 9.

## Preparazione

```bash
sudo -u postgres psql -c "CREATE ROLE saas LOGIN PASSWORD 'saas' CREATEDB"
sudo -u postgres psql -c "CREATE DATABASE saas OWNER saas"
uv sync
uv run manage.py migrate
uv run manage.py crea_demo
uv run manage.py runserver
```

Poi apri http://acme.localhost:8000 (utente `admin@acme.test`, password `password`;
analogamente `rossi.localhost`). Per l'API:

```bash
TOKEN=$(uv run manage.py crea_chiave acme admin@acme.test)
curl -H "Authorization: Bearer $TOKEN" "http://acme.localhost:8000/api/v1/tickets?limit=2"
```

Se la porta del tuo PostgreSQL non è la 5432, imposta `DB_PORT`.

## Test

```bash
uv run pytest
```

70 test. La suite usa `FETCH_RAISE` (una query nascosta è un errore) e due tenant in ogni test.

## Esperimenti

Si lanciano dalla radice del progetto, con `uv run python -m esperimenti.<nome>`:
`fetch_modes`, `paginazione`, `annotazioni` (servono i dati di `crea_demo`), `rls`
(la prova finale col superutente richiede `SUPER_DSN`).
