# Rubrica (Capitolo 4)

Django 6.1 · Python 3.14 · SQLite

Codice del capitolo corrispondente del libro. Avvio:

```
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

Il progetto usa SQLite: non serve installare né configurare nessun database.

Se la porta 8000 è occupata, avvia il server su un'altra porta, per esempio:

```
uv run python manage.py runserver 8011
```
