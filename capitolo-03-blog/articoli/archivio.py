import json
from pathlib import Path

from compression import zstd

from .models import Articolo


def scrivi_archivio(percorso: Path) -> int:
    """Salva gli articoli pubblicati in un file JSON compresso con Zstandard."""
    articoli = Articolo.objects.filter(pubblicato=True).values(
        "titolo", "slug", "sommario", "testo", "tags", "pubblicato_il"
    )
    dati = [
        {**articolo, "pubblicato_il": articolo["pubblicato_il"].isoformat()}
        for articolo in articoli
    ]
    with zstd.open(percorso, "wt", encoding="utf-8") as file:
        json.dump(dati, file, ensure_ascii=False)
    return len(dati)


def leggi_archivio(percorso: Path) -> list[dict]:
    """Legge un archivio creato da scrivi_archivio()."""
    with zstd.open(percorso, "rt", encoding="utf-8") as file:
        return json.load(file)
