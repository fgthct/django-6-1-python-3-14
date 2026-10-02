# Knowledge base con ricerca semantica (Capitolo 7)

Django 6.1 · Python 3.14 · PostgreSQL 18 + pgvector · fastembed · HTMX

```
uv sync
createdb / creare ruolo e database `kb` (vedi capitolo)
uv run manage.py migrate
uv run manage.py importa            # chunk + embedding dei documenti in documenti/
uv run manage.py runserver
uv run pytest                       # 62 test, nessun download di modelli
KB_MODELLO_VERO=1 uv run pytest -m modello_vero   # prova col modello vero
uv run python -m esperimenti.valuta # confronto fra le strategie di ricerca
```

Variabili d'ambiente: `DB_NAME` (default `kb`), `DB_PORT` (default 5432), `EMBEDDING_CACHE`, `RAG_GENERATORE`
(`estrattivo` o `ollama`), `OLLAMA_URL`, `OLLAMA_MODELLO`.

`UUID7()` richiede PostgreSQL 18 o superiore.
