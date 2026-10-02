from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from documenti import servizi
from documenti.models import Documento

User = get_user_model()

UTENTI = [("marta", "Marta", "Rossi"), ("luca", "Luca", "Bianchi"), ("giulia", "Giulia", "Verdi"),
          ("paolo", "Paolo", "Neri")]

POLITICA_FERIE = """Politica ferie

Ogni dipendente ha diritto a ventisei giorni di ferie all'anno. Le richieste si presentano al proprio responsabile con almeno due settimane di anticipo.

Le ferie non godute entro il trentuno marzo dell'anno successivo decadono, salvo accordo scritto con le risorse umane.
"""

LAYOUT_MAGAZZINO = """Layout del magazzino

Il nuovo layout dispone le scaffalature in file parallele ai baie di carico, con corsie larghe tre metri per i carrelli elevatori.

I prodotti ad alta rotazione stanno vicino alle baie, quelli stagionali nel fondo. Il materiale infiammabile va nell'area recintata a nord.
"""


class Command(BaseCommand):
    help = "Quattro utenti (password «password») e due documenti di prova."

    def handle(self, *args, **opzioni):
        utenti = {}
        for username, nome, cognome in UTENTI:
            utente, nuovo = User.objects.get_or_create(
                username=username, defaults={"first_name": nome, "last_name": cognome, "email": f"{username}@esempio.test"})
            if nuovo:
                utente.set_password("password")
                utente.save()
            utenti[username] = utente
        for proprietario, titolo, testo in [("marta", "Politica ferie", POLITICA_FERIE),
                                            ("luca", "Layout del magazzino", LAYOUT_MAGAZZINO)]:
            if not Documento.objects.filter(titolo=titolo).exists():
                servizi.crea_documento(utenti[proprietario], titolo, ContentFile(testo.encode(), name=f"{titolo}.txt"), "Prima stesura")
        self.stdout.write("Demo pronta: marta, luca, giulia, paolo (password «password»).")
