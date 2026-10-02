from pathlib import Path

from django.core.management.base import BaseCommand

from campagne.importazione import importa_csv


class Command(BaseCommand):
    help = "Importa un CSV (colonne: email,nome) validandolo in parallelo."

    def add_arguments(self, parser):
        parser.add_argument("csv", type=Path)

    def handle(self, *args, csv, **opts):
        e = importa_csv(csv)
        self.stdout.write(
            f"{e.righe} righe: {e.nuovi} nuovi, {e.gia_presenti} già presenti, "
            f"{e.duplicati_nel_file} duplicati nel file, {e.scartati} scartati"
        )
        for esempio in e.esempi_scarti:
            self.stdout.write(f"  scartata: {esempio}")
