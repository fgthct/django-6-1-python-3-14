import asyncio
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.exceptions import FieldFetchBlocked
from django.db import connection, models
from django.db.utils import DatabaseError
from django.test.utils import CaptureQueriesContext

from vetrina.models import Prodotto


def misura(titolo, funzione):
    with CaptureQueriesContext(connection) as q:
        try:
            risultato = funzione()
        except Exception as errore:
            risultato = f"{type(errore).__name__}"
    print(f"{titolo:<34} {len(q):>3} query   {risultato}")


def nomi(queryset):
    return len({p.categoria.nome for p in queryset})


misura("ingenuo", lambda: nomi(Prodotto.objects.all()))
misura("select_related('categoria')", lambda: nomi(Prodotto.objects.select_related("categoria")))
misura("fetch_mode(FETCH_PEERS)", lambda: nomi(Prodotto.objects.fetch_mode(models.FETCH_PEERS)))
misura("fetch_mode(FETCH_RAISE)", lambda: nomi(Prodotto.objects.fetch_mode(models.FETCH_RAISE)))


async def in_contesto_async():
    return [p.categoria.nome async for p in Prodotto.objects.fetch_mode(models.FETCH_PEERS)]


try:
    asyncio.run(in_contesto_async())
    print("FETCH_PEERS in async: nessun errore")
except Exception as errore:
    print(f"FETCH_PEERS in un ciclo async        {type(errore).__name__}: {errore}")
