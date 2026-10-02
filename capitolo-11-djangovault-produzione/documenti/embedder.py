"""L'unico punto del progetto che conosce il modello di embedding."""

import re
import zlib
from functools import lru_cache

from django.conf import settings


@lru_cache(maxsize=1)
def _modello():
    # Importato qui dentro: caricare fastembed e il modello costa secondi, e i test non devono pagarli.
    from fastembed import TextEmbedding

    return TextEmbedding(settings.EMBEDDING_MODELLO, cache_dir=settings.EMBEDDING_CACHE)


def _finto(testo):
    """Un «embedding» fatto di parole in un sacchetto: nessun significato, solo parole in comune.
    Basta per sviluppare e per i test senza scaricare un modello. Non è ricerca semantica."""
    vettore = [0.0] * settings.EMBEDDING_DIMENSIONI
    for parola in re.findall(r"\w+", testo.lower()):
        vettore[zlib.crc32(parola.encode()) % settings.EMBEDDING_DIMENSIONI] += 1.0
    norma = sum(x * x for x in vettore) ** 0.5 or 1.0
    return [x / norma for x in vettore]


def incorpora(testi):
    if settings.EMBEDDING_BACKEND == "finto":
        return [_finto(t) for t in testi]
    vettori = [v.tolist() for v in _modello().embed(testi)]
    for v in vettori:
        if len(v) != settings.EMBEDDING_DIMENSIONI:
            raise ValueError(f"Il modello restituisce {len(v)} dimensioni, ne servono {settings.EMBEDDING_DIMENSIONI}.")
    return vettori
