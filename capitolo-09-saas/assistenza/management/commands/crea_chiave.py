from django.core.management.base import BaseCommand, CommandError

from assistenza import chiavi
from assistenza.models import Membro


class Command(BaseCommand):
    help = "Crea una chiave API per un membro e la stampa (l'unica volta)."

    def add_arguments(self, parser):
        parser.add_argument("organizzazione")
        parser.add_argument("email")

    def handle(self, *args, organizzazione, email, **opzioni):
        try:
            membro = Membro.objects.get(organizzazione__slug=organizzazione, user__email=email)
        except Membro.DoesNotExist:
            raise CommandError("membro non trovato") from None
        self.stdout.write(chiavi.crea_chiave(membro))
