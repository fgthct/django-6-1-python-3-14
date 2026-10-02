import os
from pathlib import Path

from django.utils.csp import CSP

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-solo-per-il-libro")
DEBUG = os.environ.get("DEBUG", "1") == "1"

# Ogni cliente (tenant) vive su un sottodominio: acme.localhost, rossi.localhost.
DOMINIO_BASE = os.environ.get("DOMINIO_BASE", "localhost")
ALLOWED_HOSTS = [DOMINIO_BASE, f".{DOMINIO_BASE}"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "assistenza",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "assistenza.middleware.TenantMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

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
        "NAME": "saas",
        "USER": "saas",
        "PASSWORD": "saas",
        "HOST": "localhost",
        "PORT": os.environ.get("DB_PORT", "5433"),
    }
}

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "it"
TIME_ZONE = "Europe/Rome"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

# I cookie vivono sul sottodominio: ogni tenant ha la sua sessione.
# (Non impostare SESSION_COOKIE_DOMAIN: condividerebbe la sessione fra i tenant.)

# Mailer: il catalogo fra cui ogni tenant sceglie (vedi Organizzazione.mailer).
MAILERS = {
    "default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"},
    "dedicato": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": os.environ.get("SMTP_HOST", "localhost"),
            "port": int(os.environ.get("SMTP_PORT", "1025")),
            "timeout": 10,
        },
    },
}
EMAIL_DA = "assistenza@esempio.test"

TASKS = {"default": {"BACKEND": "django.tasks.backends.immediate.ImmediateBackend"}}

# Regola di progetto sui fetch mode: "FETCH_PEERS" in produzione (le query che
# ci sfuggono diventano una sola query, non N), "FETCH_RAISE" nei test (diventano
# un errore, e ce ne accorgiamo).
MODALITA_FETCH = os.environ.get("MODALITA_FETCH", "FETCH_PEERS")

# Django Ninja: senza questi due valori un client può chiedere limit=1000000 (il tetto predefinito è infinito).
NINJA_PAGINATION_PER_PAGE = 20
NINJA_PAGINATION_MAX_LIMIT = 100

# Content Security Policy: tutto dal nostro dominio, gli script solo con il nonce.
SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF, CSP.NONCE],
    "style-src": [CSP.SELF],
    "img-src": [CSP.SELF, "data:"],
    "connect-src": [CSP.SELF],
    "font-src": [CSP.SELF],
    "object-src": [CSP.NONE],
    "base-uri": [CSP.SELF],
    "form-action": [CSP.SELF],
    "frame-ancestors": [CSP.NONE],
    "report-uri": ["/csp-report/"],
}
# La politica «candidata»: più severa, solo in osservazione. Raccoglie le
# violazioni senza bloccare nulla, prima di decidere se renderla obbligatoria.
SECURE_CSP_REPORT_ONLY = {
    "default-src": [CSP.NONE],
    "script-src": [CSP.SELF, CSP.NONCE],
    "style-src": [CSP.SELF],
    "img-src": [CSP.SELF],
    "connect-src": [CSP.SELF],
    "require-trusted-types-for": ["'script'"],
    "report-uri": ["/csp-report/"],
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
