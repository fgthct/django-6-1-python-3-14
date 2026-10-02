from datetime import timedelta

from django.core.management.base import BaseCommand

from campagne.recupero import riaccoda_perdute


class Command(BaseCommand):
    help = "Rimette in coda le consegne perdute (worker ucciso, coda svuotata)."

    def add_arguments(self, parser):
        parser.add_argument("--minuti", type=int, default=5)

    def handle(self, *args, minuti, **opts):
        n = riaccoda_perdute(timedelta(minutes=minuti))
        self.stdout.write(f"{n} consegne rimesse in coda")
