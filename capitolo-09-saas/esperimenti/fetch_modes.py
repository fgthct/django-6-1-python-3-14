"""Lo stesso codice «distratto» con i tre fetch mode: quante query, e che cosa succede."""

from esperimenti import prelude  # noqa: F401
from django.db import connection, models, reset_queries
from django.test.utils import CaptureQueriesContext

from assistenza import tenant
from assistenza.models import Organizzazione, Ticket

org = Organizzazione.objects.get(slug="acme")


def assegnatari(qs):
    # Il codice distratto: dimentica select_related e tocca t.assegnato dentro il ciclo.
    return [t.assegnato.user.email if t.assegnato else "—" for t in qs]


with tenant.tenant(org):
    m = list(org.membri.all())
    for i, t in enumerate(Ticket.objects.all()[:10]):
        t.assegnato = m[i % 3]
        t.save(update_fields=["assegnato"])
    for nome, modalita in [("FETCH_ONE (il comportamento di sempre)", models.FETCH_ONE),
                           ("FETCH_PEERS", models.FETCH_PEERS), ("FETCH_RAISE", models.FETCH_RAISE)]:
        qs = Ticket.objects.all().fetch_mode(modalita)[:10]
        with CaptureQueriesContext(connection) as q:
            try:
                assegnatari(qs)
                esito = "ok"
            except Exception as e:  # noqa: BLE001
                esito = f"{type(e).__name__}: {e}"
        print(f"{nome:40} query: {len(q):2}   {esito}")
    qs = Ticket.objects.select_related("assegnato__user")[:10]
    with CaptureQueriesContext(connection) as q:
        assegnatari(qs.fetch_mode(models.FETCH_RAISE))
    print(f"{'select_related + FETCH_RAISE':40} query: {len(q):2}   ok")
