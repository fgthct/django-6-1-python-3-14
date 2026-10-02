# syntax=docker/dockerfile:1

# --- Stadio 1: costruzione -------------------------------------------------------------------------------
FROM python:3.14-slim AS costruzione
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Prima solo i file delle dipendenze: finché non cambiano, questo strato resta in cache.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

# Poi il codice, e i file statici con la loro impronta (chiavi finte: servono solo a far partire Django).
COPY . .
RUN SECRET_KEY=solo-per-la-costruzione ALLOWED_HOSTS=costruzione SMTP_HOST=costruzione \
    /app/.venv/bin/python manage.py collectstatic --noinput

# --- Stadio 2: l'immagine che gira -----------------------------------------------------------------------
FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    MEDIA_ROOT=/dati/media \
    EMBEDDING_CACHE=/dati/modelli

# Un utente senza privilegi: se qualcuno rompe l'applicazione, non è root nel container.
RUN useradd --system --uid 10001 --home-dir /app vault \
    && mkdir -p /dati/media /dati/modelli \
    && chown -R vault /dati

WORKDIR /app
COPY --from=costruzione --chown=vault /app /app
USER vault

VOLUME /dati
EXPOSE 8000

# Il controllo usa Python (nell'immagine non c'è curl) e interroga /salute/ con un Host consentito.
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request as u; r = u.Request('http://127.0.0.1:8000/salute/', headers={'Host': os.environ['ALLOWED_HOSTS'].split(',')[0]}); u.urlopen(r, timeout=3)" || exit 1

CMD ["gunicorn", "config.wsgi:application"]
