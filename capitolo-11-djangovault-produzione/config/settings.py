import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.utils.csp import CSP

from . import ambiente

BASE_DIR = Path(__file__).resolve().parent.parent

# Fail closed: se nessuno dice «sviluppo», si è in produzione.
DEBUG = ambiente.booleano("DEBUG", False)

if DEBUG:
    SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-solo-per-lo-sviluppo")
    ALLOWED_HOSTS = ambiente.lista("ALLOWED_HOSTS", ["localhost", "127.0.0.1"])
else:
    SECRET_KEY = ambiente.obbligatoria("SECRET_KEY")
    ALLOWED_HOSTS = ambiente.lista("ALLOWED_HOSTS")
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured("Manca ALLOWED_HOSTS: in produzione è obbligatoria.")
CSRF_TRUSTED_ORIGINS = ambiente.lista("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "documenti",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if not DEBUG:  # in sviluppo i file statici li serve runserver; in produzione WhiteNoise, subito dopo la sicurezza
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.csp",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "vault"),
        "USER": os.environ.get("DB_USER", "vault"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "vault" if DEBUG else ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        # Una connessione per worker, riusata per un minuto e controllata prima dell'uso.
        "CONN_MAX_AGE": ambiente.intero("DB_CONN_MAX_AGE", 60),
        "CONN_HEALTH_CHECKS": True,
    }
}

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "it"
TIME_ZONE = "Europe/Rome"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = Path(os.environ.get("STATIC_ROOT", BASE_DIR / "staticfiles"))
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # In produzione i nomi dei file statici portano un'impronta (vault.3f9a1c.css): cache per sempre, senza rischi.
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

# I file caricati NON hanno un MEDIA_URL: non si servono mai direttamente, ma da una vista che controlla i permessi.
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "media"))
DIMENSIONE_MASSIMA_FILE = 2 * 1024 * 1024

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "elenco"
LOGOUT_REDIRECT_URL = "login"

if DEBUG:
    MAILERS = {"default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"}}
else:
    MAILERS = {
        "default": {
            "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "OPTIONS": {
                "host": ambiente.obbligatoria("SMTP_HOST"),
                "port": ambiente.intero("SMTP_PORT", 587),
                "username": os.environ.get("SMTP_USER", ""),
                "password": os.environ.get("SMTP_PASSWORD", ""),
                "use_tls": ambiente.booleano("SMTP_TLS", True),
                "timeout": 10,  # una posta lenta non deve tenere occupato un worker per minuti
            },
        }
    }
EMAIL_DA = os.environ.get("EMAIL_DA", "vault@esempio.test")
TASKS = {"default": {"BACKEND": "django.tasks.backends.immediate.ImmediateBackend"}}

# Embedding: come nel Capitolo 7, il modello è una scelta di progetto.
EMBEDDING_MODELLO = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
EMBEDDING_DIMENSIONI = 768
# "fastembed" (il modello vero) oppure "finto" (sacchetto di parole, solo per sviluppo e test).
EMBEDDING_BACKEND = os.environ.get("EMBEDDING_BACKEND", "fastembed")
EMBEDDING_CACHE = os.environ.get("EMBEDDING_CACHE", str(BASE_DIR / ".modelli"))
RAG_DISTANZA_MASSIMA = 0.6

SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF, CSP.NONCE],
    "style-src": [CSP.SELF],
    "img-src": [CSP.SELF, "data:"],
    "connect-src": [CSP.SELF],
    "object-src": [CSP.NONE],
    "base-uri": [CSP.SELF],
    "form-action": [CSP.SELF],
    "frame-ancestors": [CSP.NONE],
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Produzione ----------------------------------------------------------------------------------------
# Il proxy (Caddy) termina il TLS e scrive X-Forwarded-Proto. Ci si può fidare di quell'intestazione SOLO
# se il proxy la sovrascrive sempre e il server dell'applicazione non è raggiungibile se non attraverso di lui.
if ambiente.booleano("TRUST_PROXY_SSL", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    SECURE_SSL_REDIRECT = ambiente.booleano("SECURE_SSL_REDIRECT", True)
    SECURE_REDIRECT_EXEMPT = [r"^salute/$", r"^pronto/$"]  # i controlli interni arrivano in HTTP
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # HSTS: si comincia con poco (un'ora) e si alza quando si è sicuri; un errore dura quanto il valore scelto.
    SECURE_HSTS_SECONDS = ambiente.intero("SECURE_HSTS_SECONDS", 3600)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = ambiente.booleano("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
    SECURE_HSTS_PRELOAD = False
    SILENCED_SYSTEM_CHECKS = ["security.W005", "security.W021"]  # scelte deliberate, spiegate nel capitolo

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"riga": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "riga"}},
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
    "loggers": {"django.request": {"level": "WARNING"}},
}
