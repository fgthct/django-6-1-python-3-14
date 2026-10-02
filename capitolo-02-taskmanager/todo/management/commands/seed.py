from datetime import date, timedelta

from django.core.management.base import BaseCommand

from todo.models import Attivita, Progetto


class Command(BaseCommand):
    help = "Crea dati di esempio: 3 progetti e 30 attività."

    def handle(self, *args, **options):
        oggi = date.today()
        progetti = [
            Progetto.objects.get_or_create(nome=nome)[0]
            for nome in ("Casa", "Lavoro", "Libro")
        ]
        for i in range(30):
            Attivita.objects.create(
                progetto=progetti[i % 3],
                titolo=f"Attività di esempio {i + 1}",
                scadenza=oggi + timedelta(days=i),
                completata=(i % 5 == 0),
            )
        self.stdout.write(self.style.SUCCESS("Dati di esempio creati."))
