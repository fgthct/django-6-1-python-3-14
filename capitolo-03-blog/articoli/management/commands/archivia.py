from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from articoli.archivio import scrivi_archivio


class Command(BaseCommand):
    help = "Archivia gli articoli pubblicati in un file .json.zst"

    def add_arguments(self, parser):
        parser.add_argument(
            "--destinazione",
            default=f"archivio-{date.today():%Y%m%d}.json.zst",
            help="percorso del file da creare",
        )

    def handle(self, *args, **opzioni):
        percorso = Path(opzioni["destinazione"])
        totale = scrivi_archivio(percorso)
        dimensione = percorso.stat().st_size
        self.stdout.write(
            self.style.SUCCESS(f"{totale} articoli archiviati in {percorso} ({dimensione} byte)")
        )
