"""MAILERS: più mailer con nome, come CACHES e DATABASES."""
from django.core import mail
from django.core.mail import mailers, send_mail

from esperimenti import prelude  # noqa: F401

for alias in ("default", "campagne"):
    m = mailers[alias]
    opzioni = {k: getattr(m, k) for k in ("host", "port") if hasattr(m, k)}
    print(f"mailers[{alias!r}] → {type(m).__module__}.{type(m).__name__} {opzioni}")

print("\nsend_mail(..., using='default') sul terminale:")
send_mail("Oggetto", "Corpo del messaggio", "a@example.com", ["b@example.com"], using="default")

print("\nun alias che non esiste:")
try:
    mailers["marketing"]
except Exception as errore:
    print(f"  {type(errore).__name__}: {errore}")

print("\nil vecchio e il nuovo non si mescolano:")
import warnings

from django.core.mail import get_connection

try:
    send_mail("s", "b", "a@example.com", ["b@example.com"], fail_silently=True, using="default")
except TypeError as errore:
    print(f"  TypeError: {errore}")

with warnings.catch_warnings(record=True) as avvisi:
    warnings.simplefilter("always")
    get_connection()
    for a in avvisi:
        print(f"  {a.category.__name__}: {str(a.message)[:100]}")
