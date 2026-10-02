"""Validazione dei contatti: Python puro, senza Django.

Questo modulo non importa nulla del progetto di proposito. Verrà eseguito
dentro un *subinterpreter*, dove Django non è configurato e il database non
esiste: tutto ciò che serve deve arrivare dagli argomenti.
"""
import re
import unicodedata

_EMAIL = re.compile(r"^[a-z0-9._%+\-]+@[^@\s]+\.[^@\s.]{2,}$")


def valida_blocco(righe: list[tuple[str, str]]) -> list[tuple[str | None, str, str | None]]:
    """Per ogni riga (email, nome) restituisce (email normalizzata, nome, errore).

    Se la riga non è valida l'email è `None` e l'errore dice perché.
    """
    esiti = []
    for email, nome in righe:
        nome_pulito = " ".join(unicodedata.normalize("NFKC", nome).split()).title()
        grezza = unicodedata.normalize("NFKC", email).strip().lower()
        locale, _, dominio = grezza.rpartition("@")
        try:
            # I domini internazionali (es. «bücher.example») viaggiano come punycode.
            dominio_ascii = dominio.encode("idna").decode("ascii")
        except UnicodeError:
            esiti.append((None, nome_pulito, "dominio non valido"))
            continue
        normalizzata = f"{locale}@{dominio_ascii}"
        if not _EMAIL.match(normalizzata):
            esiti.append((None, nome_pulito, "indirizzo non valido"))
        elif not nome_pulito:
            esiti.append((None, nome_pulito, "nome mancante"))
        else:
            esiti.append((normalizzata, nome_pulito, None))
    return esiti
