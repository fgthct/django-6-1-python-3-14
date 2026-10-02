from django.db import transaction
from django.tasks import task

from .chunking import spezza
from .embedder import incorpora
from .models import Chunk, Versione


@task
def indicizza_versione(versione_id):
    """Spezza il testo di una versione e ne calcola i vettori. Si può ripetere senza danni."""
    versione = Versione.objects.get(pk=versione_id)
    passaggi = spezza(versione.testo)
    vettori = incorpora(passaggi) if passaggi else []
    with transaction.atomic():
        versione.chunk.all().delete()
        Chunk.objects.bulk_create(
            Chunk(versione=versione, posizione=i, testo=t, embedding=v)
            for i, (t, v) in enumerate(zip(passaggi, vettori, strict=True))
        )
    return len(passaggi)
