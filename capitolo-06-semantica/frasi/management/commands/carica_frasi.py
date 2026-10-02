from django.core.management.base import BaseCommand

from frasi.corpus import CORPUS
from frasi.embedder import incorpora
from frasi.models import Frase


class Command(BaseCommand):
    help = "Carica le frasi di prova e ne calcola gli embedding (idempotente)."

    def handle(self, *args, **opzioni):
        for argomento, testi in CORPUS.items():
            for testo in testi:
                Frase.objects.get_or_create(testo=testo, defaults={"argomento": argomento})
        da_fare = list(Frase.objects.filter(embedding=None))
        if da_fare:
            vettori = incorpora([f.testo for f in da_fare])
            for frase, vettore in zip(da_fare, vettori, strict=True):
                frase.embedding = vettore
            Frase.objects.bulk_update(da_fare, ["embedding"])
        self.stdout.write(f"{Frase.objects.count()} frasi, {len(da_fare)} embedding calcolati.")
