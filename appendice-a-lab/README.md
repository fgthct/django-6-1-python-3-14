# Laboratorio di aggiornamento (Appendice A)

Un progetto minimo con le funzionalità che cambiano fra Django 5.2, 6.0 e 6.1.

    uv venv .venv5.2 && uv pip install --python .venv5.2/bin/python "django>=5.2,<5.3"
    uv venv .venv6.0 && uv pip install --python .venv6.0/bin/python "django>=6.0,<6.1"
    uv venv .venv6.1 && uv pip install --python .venv6.1/bin/python "django>=6.1,<6.2"
    .venv5.2/bin/python prova.py
    .venv6.0/bin/python prova.py
    .venv6.1/bin/python prova.py
    .venv6.1/bin/python manage.py makemigrations --check --dry-run

La migrazione `demo/migrations/0001_initial.py` è stata generata con Django 5.2 senza `DEFAULT_AUTO_FIELD`: con 6.0 e 6.1 il controllo delle migrazioni la segnala.
