import re
from dataclasses import dataclass

from django.contrib.postgres.search import SearchQuery, SearchRank
from pgvector.django import CosineDistance

from .embedder import incorpora
from .models import Chunk


def cerca_per_significato(domanda: str, limite: int = 20, vettore=None):
    if vettore is None:
        vettore = incorpora([domanda])[0]
    return (
        Chunk.objects.exclude(embedding=None)
        .select_related("documento")
        .annotate(distanza=CosineDistance("embedding", vettore))
        .order_by("distanza", "pk")[:limite]
    )


def cerca_per_parole(domanda: str, limite: int = 20, tutte_le_parole: bool = False):
    """Full-text search sul testo dei chunk.

    Con `websearch` PostgreSQL mette in AND tutte le parole: una domanda in
    linguaggio naturale («Quanti giorni di vacanza spettano in un anno?») non
    trova mai niente, perché nessun passaggio le contiene tutte. Per una
    domanda basta che ne contenga *qualcuna*: le uniamo con `or` e lasciamo a
    ts_rank il compito di mettere in cima chi ne ha di più.
    """
    if tutte_le_parole:
        testo = domanda
    else:
        testo = " or ".join(re.findall(r"[\w@.\-:]+", domanda))
    query = SearchQuery(testo, config="italian", search_type="websearch")
    return (
        Chunk.objects.filter(ricerca=query)
        .select_related("documento")
        .annotate(rango=SearchRank("ricerca", query))
        .order_by("-rango", "pk")[:limite]
    )


def fusione_rrf(classifiche: list[list], k: int = 60) -> list[tuple]:
    """Reciprocal Rank Fusion: ogni elemento prende 1/(k + posizione) da ogni classifica.

    Non guarda i punteggi, solo le posizioni: per questo funziona anche se una
    classifica parla di distanze coseno e l'altra di ts_rank, che non sono
    confrontabili. Restituisce [(elemento, punteggio)] dal migliore.
    """
    punteggi: dict = {}
    for classifica in classifiche:
        for posizione, elemento in enumerate(classifica, start=1):
            punteggi[elemento] = punteggi.get(elemento, 0.0) + 1.0 / (k + posizione)
    # A parità di punteggio vince l'elemento comparso prima: l'ordine è stabile.
    return sorted(punteggi.items(), key=lambda coppia: -coppia[1])


@dataclass
class Risultato:
    chunk: Chunk
    punteggio: float
    posizione_significato: int | None
    posizione_parole: int | None


def cerca_ibrida(
    domanda: str, limite: int = 5, candidati: int = 20, vettore=None, tutte_le_parole: bool = True
) -> list[Risultato]:
    semantici = list(cerca_per_significato(domanda, candidati, vettore))
    testuali = list(cerca_per_parole(domanda, candidati, tutte_le_parole))
    pos_s = {c.pk: i for i, c in enumerate(semantici, start=1)}
    pos_t = {c.pk: i for i, c in enumerate(testuali, start=1)}
    per_id = {c.pk: c for c in [*semantici, *testuali]}
    fusa = fusione_rrf([[c.pk for c in semantici], [c.pk for c in testuali]])
    return [
        Risultato(per_id[pk], punteggio, pos_s.get(pk), pos_t.get(pk))
        for pk, punteggio in fusa[:limite]
    ]
