import json
import urllib.request
from dataclasses import dataclass, field

from django.conf import settings

from .embedder import incorpora
from .prompt import prompt_rag
from .ricerca import Risultato, cerca_ibrida, cerca_per_significato

NON_LO_SO = "Non ho trovato nella knowledge base nulla che risponda a questa domanda."


@dataclass
class Risposta:
    testo: str
    fonti: list[Risultato] = field(default_factory=list)
    trovata: bool = True


def genera_estrattivo(prompt: str, passaggi: list[str]) -> str:
    """Nessun modello generativo: la risposta è il passaggio più pertinente, così com'è."""
    return passaggi[0]


def genera_ollama(prompt: str, passaggi: list[str]) -> str:
    richiesta = urllib.request.Request(
        f"{settings.OLLAMA_URL}/api/generate",
        data=json.dumps(
            {"model": settings.OLLAMA_MODELLO, "prompt": prompt, "stream": False}
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(richiesta, timeout=120) as risposta:
        return json.load(risposta)["response"].strip()


GENERATORI = {"estrattivo": genera_estrattivo, "ollama": genera_ollama}


def rispondi(domanda: str) -> Risposta:
    # Il vettore della domanda lo calcoliamo una volta sola e lo riusiamo.
    vettore = incorpora([domanda])[0]
    migliore = list(cerca_per_significato(domanda, 1, vettore))
    if not migliore or migliore[0].distanza > settings.RAG_DISTANZA_MASSIMA:
        return Risposta(NON_LO_SO, [], trovata=False)

    fonti = cerca_ibrida(domanda, settings.RAG_CHUNK_NEL_CONTESTO, vettore=vettore)
    passaggi = [r.chunk.testo for r in fonti]
    prompt = prompt_rag(domanda, passaggi)
    testo = GENERATORI[settings.RAG_GENERATORE](prompt, passaggi)
    return Risposta(testo, fonti)
