"""L'unico punto del progetto che conosce il modello di embedding."""
from functools import lru_cache

from django.conf import settings


@lru_cache(maxsize=1)
def _modello():
    # L'importazione è qui dentro: caricare fastembed e il modello costa secondi,
    # e i test, le migrazioni e i comandi che non cercano non devono pagarli.
    from fastembed import TextEmbedding

    return TextEmbedding(settings.EMBEDDING_MODELLO, cache_dir=settings.EMBEDDING_CACHE)


def incorpora(testi: list[str]) -> list[list[float]]:
    """Trasforma una lista di testi in una lista di vettori (liste di float)."""
    vettori = [v.tolist() for v in _modello().embed(testi)]
    for v in vettori:
        if len(v) != settings.EMBEDDING_DIMENSIONI:
            raise ValueError(
                f"Il modello restituisce {len(v)} dimensioni, "
                f"ma il progetto ne aspetta {settings.EMBEDDING_DIMENSIONI}."
            )
    return vettori
