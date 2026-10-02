"""Lo stesso risultato, due piani: l'indice HNSW salta i NULL, la scansione no."""
from django.db import connection, transaction
from pgvector.django import CosineDistance

from esperimenti import prelude  # noqa: F401
from conoscenza.embedder import incorpora
from conoscenza.models import Chunk

v = incorpora(["ferie"])[0]


def senza_exclude():
    return Chunk.objects.annotate(d=CosineDistance("embedding", v)).order_by("d")[:30]


def conta(indice: bool):
    with connection.cursor() as c:
        c.execute("SET LOCAL enable_seqscan = %s" % ("off" if indice else "on"))
        c.execute("SET LOCAL enable_indexscan = %s" % ("on" if indice else "off"))
        c.execute("SET LOCAL enable_bitmapscan = %s" % ("on" if indice else "off"))
    return len(list(senza_exclude()))


with transaction.atomic():
    Chunk.objects.filter(posizione=0).update(embedding=None)  # 6 chunk senza vettore
    print("chunk totali:", Chunk.objects.count(), "- senza vettore:", Chunk.objects.filter(embedding=None).count())
    print("scansione sequenziale :", conta(indice=False), "risultati")
    print("indice HNSW           :", conta(indice=True), "risultati")
    print("con exclude(NULL)     : sempre", Chunk.objects.exclude(embedding=None).count())
    transaction.set_rollback(True)
