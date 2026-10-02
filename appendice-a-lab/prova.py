"""Ogni sonda usa una funzionalità che cambia fra 5.2, 6.0 e 6.1, e riporta che cosa succede."""
import os, warnings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.core import mail
from django.core.files import File
from django.core.management import call_command
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password
from django.db import connection, models, transaction
from django.db.models import Q
from django.template import Context, Engine
from django.test.utils import CaptureQueriesContext
from django.urls import register_converter
from django.utils.html import format_html
from demo.models import Nota

call_command("migrate", verbosity=0)
Nota.objects.create(titolo="a")


def sonda_save_posizionale():
    Nota(titolo="b").save(False, False)

def sonda_format_html_senza_argomenti():
    format_html("<b>x</b>")

def sonda_checkconstraint_check():
    models.CheckConstraint(check=Q(titolo="x"), name="c")

def sonda_is_iterable():
    from django.utils.itercompat import is_iterable  # noqa

class Conv:
    regex = "[0-9]+"
    def to_python(self, v): return int(v)
    def to_url(self, v): return str(v)

def sonda_register_converter_due_volte():
    register_converter(Conv, "numero"); register_converter(Conv, "numero")

def sonda_email_argomenti_posizionali():
    mail.EmailMessage("s", "b", "a@esempio.it", ["b@esempio.it"], ["c@esempio.it"])

def sonda_admins_come_tuple():
    mail.mail_admins("s", "b")

def sonda_orphans():
    Paginator(range(10), 5, orphans=5)

def sonda_badheadererror():
    from django.core.mail import BadHeaderError  # noqa

def sonda_select_related_senza_argomenti():
    Nota.objects.select_related()

def sonda_values_list_flat_senza_campo():
    Nota.objects.values_list(flat=True)

def sonda_savepoint():
    with transaction.atomic():
        sid = transaction.savepoint(); transaction.savepoint_commit(sid)

def sonda_doppio_punto_nei_template():
    Engine().from_string("{{ a..b }}").render(Context({"a": {"": {"b": 1}}}))

def sonda_get_connection():
    mail.get_connection()

def sonda_fail_silently():
    mail.send_mail("s", "b", "a@esempio.it", ["b@esempio.it"], fail_silently=True)

def sonda_json_none():
    Nota.objects.create(titolo="j", dati=None)

def sonda_first_senza_ordinamento():
    with CaptureQueriesContext(connection) as q:
        Nota.objects.order_by().first()
    return "ORDER BY presente" if "ORDER BY" in q[0]["sql"] else "nessun ORDER BY"

def sonda_file_vuoto_e_vero():
    return f"bool(File(None)) = {bool(File(None))}"

def sonda_iterazioni_pbkdf2():
    return "iterazioni = " + make_password("x").split("$")[1]

def sonda_urlize():
    from django.utils.html import urlize
    return urlize("esempio.it")


for nome, f in [(n, g) for n, g in sorted(globals().items()) if n.startswith("sonda_")]:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            r = f(); esito = "ok" + (f" ({r})" if r else "")
        except Exception as e:
            esito = f"ERRORE {type(e).__name__}: {str(e)[:70]}"
    avvisi = sorted({f"{x.category.__name__}" for x in w if "RemovedIn" in x.category.__name__ or "Deprecat" in x.category.__name__})
    print(f"{nome[6:]:42} {esito}" + (f"  [{', '.join(avvisi)}]" if avvisi else ""))
