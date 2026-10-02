from dataclasses import dataclass, field

from django.conf import settings

from .embedder import incorpora
from .models import Chunk
from .ricerca import cerca

NON_LO_SO = "Non ho trovato, nei documenti che puoi vedere, nulla che risponda a questa domanda."


@dataclass
class Risposta:
    testo: str
    fonti: list[Chunk] = field(default_factory=list)
    trovata: bool = True


def rispondi(utente, domanda):
    """Risposta *estrattiva*: il passaggio migliore, con le sue fonti. Un modello generativo
    (come nel Capitolo 7) si innesta qui, e riceve soltanto passaggi che l'utente può già leggere."""
    vettore = incorpora([domanda])[0]
    fonti = cerca(utente, domanda, limite=3, vettore=vettore)
    if not fonti or fonti[0].distanza > settings.RAG_DISTANZA_MASSIMA:
        return Risposta(NON_LO_SO, [], trovata=False)
    return Risposta(fonti[0].testo, fonti)
