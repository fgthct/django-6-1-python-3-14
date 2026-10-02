from django.core.management.base import BaseCommand

from frasi.ricerca import cerca_per_parole, cerca_per_significato


class Command(BaseCommand):
    help = "Cerca nelle frasi, per significato e (con --confronta) anche per parole."

    def add_arguments(self, parser):
        parser.add_argument("domanda")
        parser.add_argument("--confronta", action="store_true")
        parser.add_argument("--limite", type=int, default=5)

    def handle(self, *args, domanda, confronta, limite, **opzioni):
        self.stdout.write(f"Domanda: {domanda}\n")
        self.stdout.write("Per significato (distanza coseno):")
        for f in cerca_per_significato(domanda, limite):
            self.stdout.write(f"  {f.distanza:.3f}  [{f.argomento}] {f.testo}")
        if confronta:
            self.stdout.write("\nPer parole (full-text, config italian):")
            trovate = list(cerca_per_parole(domanda, limite))
            for f in trovate:
                self.stdout.write(f"  {f.rango:.3f}  [{f.argomento}] {f.testo}")
            if not trovate:
                self.stdout.write("  (nessun risultato)")
