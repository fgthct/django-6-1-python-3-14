import hashlib
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from conoscenza.chunking import dividi, da_incorporare
from conoscenza.embedder import incorpora
from conoscenza.models import Chunk, Documento


class Command(BaseCommand):
    help = "Importa i documenti Markdown di una cartella: chunk + embedding. Idempotente."

    def add_arguments(self, parser):
        parser.add_argument("cartella", nargs="?", default="documenti")
        parser.add_argument("--forza", action="store_true", help="rifà anche i documenti invariati")
        parser.add_argument("--elimina-orfani", action="store_true",
                            help="cancella i documenti che non sono più nella cartella")

    def handle(self, *args, cartella, forza, elimina_orfani, **opts):
        file = sorted(Path(cartella).glob("*.md"))
        nuovi = aggiornati = saltati = 0
        for f in file:
            esito = self.importa_file(f, forza)
            nuovi += esito == "nuovo"
            aggiornati += esito == "aggiornato"
            saltati += esito == "invariato"
        eliminati = 0
        if elimina_orfani:
            presenti = [f.name for f in file]
            eliminati, _ = Documento.objects.exclude(percorso__in=presenti).delete()
        self.stdout.write(
            f"{nuovi} nuovi, {aggiornati} aggiornati, {saltati} invariati"
            + (f", {eliminati} righe eliminate" if elimina_orfani else "")
        )

    def importa_file(self, f: Path, forza: bool) -> str:
        contenuto = f.read_text(encoding="utf-8")
        impronta = hashlib.sha256(contenuto.encode()).hexdigest()
        esistente = Documento.objects.filter(percorso=f.name).first()
        if esistente and not forza and esistente.hash == impronta and self.aggiornato(esistente):
            return "invariato"

        titolo, pezzi = dividi(contenuto)
        vettori = incorpora([da_incorporare(titolo, p) for p in pezzi])
        with transaction.atomic():
            doc, _ = Documento.objects.update_or_create(
                percorso=f.name, defaults={"titolo": titolo or f.stem, "hash": impronta}
            )
            doc.chunk.all().delete()
            Chunk.objects.bulk_create(
                Chunk(documento=doc, posizione=i, sezione=p.sezione, testo=p.testo,
                      embedding=v, modello=settings.EMBEDDING_MODELLO)
                for i, (p, v) in enumerate(zip(pezzi, vettori))
            )
        return "aggiornato" if esistente else "nuovo"

    def aggiornato(self, doc: Documento) -> bool:
        """Il documento è invariato, ma i suoi vettori vengono dal modello attuale?"""
        return not doc.chunk.exclude(modello=settings.EMBEDDING_MODELLO).exists()
