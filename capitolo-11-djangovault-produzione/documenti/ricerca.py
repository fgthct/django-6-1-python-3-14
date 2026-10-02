from django.db import connection, transaction
from django.db.models import F
from pgvector.django import CosineDistance

from .embedder import incorpora
from .models import Chunk, Documento


def cerca(utente, domanda, limite=5, vettore=None):
    """I passaggi più vicini alla domanda, fra i soli documenti che `utente` può vedere."""
    if vettore is None:
        vettore = incorpora([domanda])[0]
    visibili = Documento.objects.visibili_a(utente)
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Senza questa riga l'indice HNSW cerca i suoi ~40 candidati *prima* di applicare il filtro
            # dei permessi, e può restituire meno risultati del dovuto, fino a zero (vedi il capitolo).
            cursor.execute("SET LOCAL hnsw.iterative_scan = 'relaxed_order'")
        risultati = list(
            Chunk.objects.filter(
                versione__documento__in=visibili,
                versione__documento__versione_corrente=F("versione"),
            )
            .exclude(embedding=None)
            .select_related("versione__documento")
            .annotate(distanza=CosineDistance("embedding", vettore))
            .order_by("distanza", "pk")[:limite]
        )
    # Con relaxed_order i risultati possono arrivare «quasi» in ordine: li rimettiamo noi.
    risultati.sort(key=lambda c: (c.distanza, c.pk))
    return risultati
