from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from pgvector.django import CosineDistance

from .embedder import incorpora
from .models import Frase


def cerca_per_significato(domanda: str, limite: int = 5, vettore=None):
    """Le frasi più vicine alla domanda, per distanza coseno (0 = identiche)."""
    if vettore is None:
        vettore = incorpora([domanda])[0]
    return (
        Frase.objects.exclude(embedding=None)
        .annotate(distanza=CosineDistance("embedding", vettore))
        .order_by("distanza", "pk")[:limite]
    )


def cerca_per_parole(domanda: str, limite: int = 5):
    """La ricerca full-text del Capitolo 3, sullo stesso corpus, per confronto."""
    query = SearchQuery(domanda, config="italian", search_type="websearch")
    vettore = SearchVector("testo", config="italian")
    return (
        Frase.objects.annotate(ricerca=vettore)
        .filter(ricerca=query)  # solo le frasi che *contengono* i termini
        .annotate(rango=SearchRank(vettore, query))
        .order_by("-rango", "pk")[:limite]
    )
