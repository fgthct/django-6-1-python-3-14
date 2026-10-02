from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from assistenza import tenant
from assistenza.models import Membro, Organizzazione, Ticket

User = get_user_model()


class Command(BaseCommand):
    help = "Due organizzazioni di prova (acme e rossi), con utenti e ticket."

    def handle(self, *args, **opzioni):
        for slug, nome in [("acme", "Acme Srl"), ("rossi", "Studio Rossi")]:
            org, _ = Organizzazione.objects.get_or_create(slug=slug, defaults={"nome": nome})
            for ruolo, nome_ruolo in [(Membro.Ruolo.ADMIN, "admin"), (Membro.Ruolo.AGENTE, "agente"),
                                      (Membro.Ruolo.LETTORE, "lettore")]:
                email = f"{nome_ruolo}@{slug}.test"
                user, creato = User.objects.get_or_create(username=email, defaults={"email": email})
                if creato:
                    user.set_password("password")
                    user.save()
                Membro.objects.get_or_create(user=user, organizzazione=org, defaults={"ruolo": ruolo})
            with tenant.tenant(org):
                if not Ticket.objects.exists():
                    for n in range(1, 26):
                        Ticket.objects.create(titolo=f"{nome}: problema {n}", richiedente=f"cliente{n}@esempio.test",
                                              priorita=(n % 3) + 1)
        self.stdout.write("Demo pronta: acme.localhost / rossi.localhost, password «password».")
