import csv
import site
from collections.abc import Callable, Iterator
from concurrent.futures import Executor, InterpreterPoolExecutor
from dataclasses import dataclass, field
from itertools import batched
from pathlib import Path

from django.conf import settings

from .models import Contatto
from .validazione import valida_blocco

DIMENSIONE_BLOCCO = 5000


@dataclass
class Esito:
    righe: int = 0
    nuovi: int = 0
    gia_presenti: int = 0
    duplicati_nel_file: int = 0
    scartati: int = 0
    esempi_scarti: list[str] = field(default_factory=list)


def leggi_righe(percorso: Path) -> Iterator[tuple[str, str]]:
    with open(percorso, newline="", encoding="utf-8") as f:
        for riga in csv.DictReader(f):
            yield riga.get("email", ""), riga.get("nome", "")


def pool_di_subinterpreter() -> InterpreterPoolExecutor:
    """Un subinterpreter parte con un `sys.path` suo, deciso all'avvio del processo.

    Dentro i test, o sotto un altro server, la cartella del progetto potrebbe
    non esserci, e allora `campagne.validazione` non si trova: lo diciamo noi
    a ogni subinterpreter, con una funzione della libreria standard che sa farlo.
    """
    return InterpreterPoolExecutor(initializer=site.addsitedir, initargs=(str(settings.BASE_DIR),))


def importa_csv(
    percorso: Path,
    *,
    esecutore: Callable[[], Executor] = pool_di_subinterpreter,
    dimensione_blocco: int = DIMENSIONE_BLOCCO,
) -> Esito:
    """Legge il CSV, valida a blocchi *in parallelo*, scrive i contatti nuovi."""
    blocchi = [list(b) for b in batched(leggi_righe(percorso), dimensione_blocco)]
    esito = Esito(righe=sum(len(b) for b in blocchi))

    visti: dict[str, str] = {}
    with esecutore() as pool:
        for blocco, esiti in zip(blocchi, pool.map(valida_blocco, blocchi)):
            for (email_grezza, _), (email, nome, errore) in zip(blocco, esiti):
                if errore:
                    esito.scartati += 1
                    if len(esito.esempi_scarti) < 5:
                        esito.esempi_scarti.append(f"{email_grezza!r}: {errore}")
                elif email in visti:
                    esito.duplicati_nel_file += 1
                else:
                    visti[email] = nome

    esistenti = set()
    chiavi = list(visti)
    for gruppo in batched(chiavi, 5000):
        esistenti.update(Contatto.objects.filter(email__in=gruppo).values_list("email", flat=True))
    esito.gia_presenti = len(esistenti)
    nuovi = [Contatto(email=e, nome=n) for e, n in visti.items() if e not in esistenti]
    Contatto.objects.bulk_create(nuovi, batch_size=2000, ignore_conflicts=True)
    esito.nuovi = len(nuovi)
    return esito
