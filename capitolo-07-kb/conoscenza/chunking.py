"""Spezza un documento Markdown in pezzi che abbiano senso da soli."""
import re
from dataclasses import dataclass

MAX_CARATTERI = 700


@dataclass(frozen=True)
class Pezzo:
    sezione: str
    testo: str


def dividi(markdown: str, max_caratteri: int = MAX_CARATTERI) -> tuple[str, list[Pezzo]]:
    """Restituisce (titolo del documento, pezzi).

    Si taglia ai titoli di sezione (`## ...`), perché è lì che l'autore ha già
    deciso dove cambia argomento. Se una sezione è troppo lunga la si divide
    ai confini dei paragrafi: mai a metà frase.
    """
    titolo = ""
    sezione = ""
    paragrafi: list[str] = []
    pezzi: list[Pezzo] = []

    def chiudi():
        pezzi.extend(_impacchetta(sezione, paragrafi, max_caratteri))
        paragrafi.clear()

    for blocco in re.split(r"\n\s*\n", markdown.strip()):
        blocco = blocco.strip()
        if not blocco:
            continue
        if blocco.startswith("# ") and not titolo:
            titolo = blocco[2:].strip()
        elif blocco.startswith("## "):
            chiudi()
            sezione = blocco[3:].strip()
        else:
            paragrafi.append(blocco)
    chiudi()
    return titolo, pezzi


def _impacchetta(sezione: str, paragrafi: list[str], massimo: int) -> list[Pezzo]:
    pezzi, corrente = [], []
    for p in paragrafi:
        # Un paragrafo più lungo del massimo resta intero: spezzarlo è peggio.
        if corrente and len("\n\n".join([*corrente, p])) > massimo:
            pezzi.append(Pezzo(sezione, "\n\n".join(corrente)))
            corrente = []
        corrente.append(p)
    if corrente:
        pezzi.append(Pezzo(sezione, "\n\n".join(corrente)))
    return pezzi


def da_incorporare(titolo: str, pezzo: Pezzo) -> str:
    """Ciò che diamo al modello di embedding: il pezzo *con il suo contesto*.

    Un paragrafo che dice «la richiesta va fatta 15 giorni prima» non dice di
    cosa parla. Titolo e sezione glielo ricordano.
    """
    intestazione = f"{titolo} — {pezzo.sezione}" if pezzo.sezione else titolo
    return f"{intestazione}\n{pezzo.testo}"
