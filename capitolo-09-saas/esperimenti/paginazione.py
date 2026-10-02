"""Paginare con LIMIT/OFFSET su un ordinamento non deterministico."""

from esperimenti import prelude  # noqa: F401
from django.db import transaction

from assistenza import tenant
from assistenza.models import Organizzazione, Ticket

org = Organizzazione.objects.get(slug="rossi")


def percorri(qs, per_pagina=10):
    visti = []
    for offset in range(0, qs.count(), per_pagina):
        visti += [t.pk for t in qs[offset:offset + per_pagina]]
    return visti


with tenant.tenant(org):
    tot = Ticket.objects.count()
    print(f"ticket del tenant: {tot}")
    for nome, qs in [("order_by('priorita')", Ticket.objects.order_by("priorita")),
                     ("order_by('priorita', 'pk')", Ticket.objects.order_by("priorita", "pk")),
                     ("ordinamento predefinito", Ticket.objects.all())]:
        print(f"{nome:28} totally_ordered={qs.totally_ordered!s:5}", end="  ")
        for giro in range(1, 4):
            visti = percorri(qs)
            print(f"giro {giro}: {len(visti)} righe, {len(set(visti))} distinte;", end=" ")
            # fra un giro e l'altro «tocchiamo» le righe, come farebbe un sistema vivo
            Ticket.objects.filter(priorita=2).update(descrizione="aggiornato")
        print()
