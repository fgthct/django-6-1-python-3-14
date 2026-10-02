# Posta: campagne email in background (Capitolo 8)

Django 6.1 · Python 3.14 · `django.tasks` + `django-tasks-db` · Redis · subinterpreter · `MAILERS`

Servono PostgreSQL (database `posta`, ruolo `posta`) e Redis.

```
uv sync
uv run manage.py migrate
uv run manage.py runserver                       # terminale 1
uv run manage.py db_worker                       # terminale 2: il worker dei task
python -m aiosmtpd -n -l localhost:1025          # terminale 3: un server SMTP di prova (stampa i messaggi)
uv run manage.py recupera_consegne               # da lanciare ogni tanto (cron)
uv run pytest                                    # 53 test; quelli su Redis si saltano se Redis non c'è
uv run python -m esperimenti.prova_completa      # worker veri, SMTP, Redis: tre scenari
```

Variabili d'ambiente: `DB_PORT`, `REDIS_URL`, `SMTP_HOST`, `SMTP_PORT`,
`CAMPAGNE_INVII_AL_SECONDO`, `CAMPAGNE_ATTESA_BASE`.
