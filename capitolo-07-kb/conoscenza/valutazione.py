"""Un piccolo insieme d'oro: domande reali, e il passaggio che deve rispondere.

Una domanda è «risolta» se uno dei primi N risultati contiene la frase `deve_contenere`.
Si controlla il testo e non l'id del chunk: se domani cambiamo il chunking,
l'insieme d'oro resta valido.
"""
import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Domanda:
    testo: str
    deve_contenere: str
    tipo: str  # "parafrasi" = poche parole in comune; "esatta" = un termine preciso


DOMANDE = [
    # Parafrasi: la domanda non usa le parole del documento.
    Domanda("Quanti giorni di vacanza spettano in un anno?", "26 giorni di ferie", "parafrasi"),
    Domanda("Se mi sento male chi devo avvisare e quando?", "entro le nove del mattino", "parafrasi"),
    Domanda("Posso lavorare dal divano di casa?", "due giorni alla settimana", "parafrasi"),
    Domanda("Quanto mi danno se vado in trasferta con la mia macchina?", "0,35 euro al chilometro", "parafrasi"),
    Domanda("Ho perso uno scontrino vecchio di due mesi, posso ancora farmelo pagare?", "dopo questo termine", "parafrasi"),
    Domanda("Quanto posso spendere per mangiare la sera fuori sede?", "35 euro", "parafrasi"),
    Domanda("Ho cliccato un link strano nella posta, che faccio?", "phishing", "parafrasi"),
    Domanda("Mi hanno rubato il computer, a chi telefono?", "4400", "parafrasi"),
    Domanda("Un cliente è arrabbiato e vuole i soldi indietro, entro quando può chiederli?", "14 giorni", "parafrasi"),
    Domanda("Quando comincio a lavorare, chi mi insegna le cose?", "affiancato da un collega", "parafrasi"),
    Domanda("Ho cancellato per sbaglio una tabella, come la recupero?", "aprire un ticket", "parafrasi"),
    Domanda("Quanto tempo ho per fare i corsi obbligatori?", "entro 30 giorni dall'assunzione", "parafrasi"),
    # Esatte: un codice, una sigla, un numero che solo le parole sanno trovare.
    Domanda("modulo RS-12", "RS-12", "esatta"),
    Domanda("RPO", "(RPO)", "esatta"),
    Domanda("pg_dump", "pg_dump", "esatta"),
    Domanda("02:30", "02:30", "esatta"),
    Domanda("sicurezza@bottegaetnea.example", "sicurezza@bottegaetnea.example", "esatta"),
    Domanda("ROL", "(ROL)", "esatta"),
]


def posizione_della_risposta(domanda: Domanda, chunk_ordinati) -> int | None:
    """La posizione (da 1) del primo chunk che risponde, o None."""
    for i, chunk in enumerate(chunk_ordinati, start=1):
        if domanda.deve_contenere in chunk.testo:
            return i
    return None


@dataclass
class Punteggio:
    hit_1: float
    hit_3: float
    mrr: float  # media di 1/posizione: 1.0 = sempre primo, 0 = mai trovato
    millisecondi: float


def valuta(strategia: Callable, domande=DOMANDE, n: int = 3) -> Punteggio:
    """`strategia(testo)` restituisce i chunk in ordine di rilevanza."""
    posizioni, tempo = [], 0.0
    for d in domande:
        t0 = time.perf_counter()
        chunk = list(strategia(d.testo))
        tempo += time.perf_counter() - t0
        posizioni.append(posizione_della_risposta(d, chunk))
    tot = len(domande)
    return Punteggio(
        hit_1=sum(p == 1 for p in posizioni) / tot,
        hit_3=sum(p is not None and p <= n for p in posizioni) / tot,
        mrr=sum(1 / p for p in posizioni if p) / tot,
        millisecondi=1000 * tempo / tot,
    )
