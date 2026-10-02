from django.core.management.base import BaseCommand

from contatti.models import Contatto

NOMI = [
    "Anna Rossi", "Bruno Bianchi", "Carla Verdi", "Davide Neri", "Elena Russo",
    "Fabio Gallo", "Giulia Conti", "Hugo Marino", "Irene Greco", "Luca Bruno",
    "Marta Costa", "Nicola Fontana", "Olga Ferri", "Paolo Riva", "Quirino Serra",
    "Rita Villa", "Sergio Moretti", "Tania Leone", "Ugo Lombardi", "Vera Barbieri",
    "Walter Sala", "Ximena Coppola", "Yari Testa", "Zoe Monti", "Aldo Pellegrini",
    "Bice Rinaldi", "Cesare Caruso", "Dora Ferrara", "Enzo Gatti", "Flavia Orlando",
    "Gino Silvestri", "Helga Bianco", "Ivo Mancini", "Lidia Basile", "Mario Sorrentino",
]
CITTA = ["Roma", "Milano", "Napoli", "Torino", "Palermo", "Bologna", "Firenze", "Bari"]


class Command(BaseCommand):
    help = "Crea contatti di prova (idempotente)."

    def handle(self, *args, **opzioni):
        creati = 0
        for i, nome in enumerate(NOMI):
            email = nome.lower().replace(" ", ".") + "@example.com"
            _, nuovo = Contatto.objects.get_or_create(
                email=email,
                defaults={"nome": nome, "citta": CITTA[i % len(CITTA)], "telefono": f"06 555{i:04d}"},
            )
            creati += nuovo
        self.stdout.write(f"{creati} contatti creati, {Contatto.objects.count()} in totale.")
