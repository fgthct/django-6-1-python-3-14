from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from articoli.models import Articolo, Categoria, Commento

ARTICOLI = [
    ("Cucina", "Arancino o arancina? Il grande dibattito",
     "A Catania si dice arancino, a Palermo arancina.",
     "Il nome cambia da una città all'altra, ma il principio è lo stesso: una palla di riso "
     "farcita, impanata e fritta. A Catania la forma è conica, come l'Etna, e il ripieno "
     "classico è ragù di carne con piselli. Le arancine al burro sono invece farcite con "
     "prosciutto e mozzarella.",
     ["arancine", "street food"]),
    ("Cucina", "Il cannolo siciliano",
     "La scorza croccante e la ricotta di pecora.",
     "Il cannolo è fatto da una scorza di pasta fritta, arrotolata attorno a una canna, e da "
     "un ripieno di ricotta di pecora zuccherata. I pasticceri più esigenti riempiono i "
     "cannoli solo al momento, per evitare che la scorza si ammorbidisca. Sopra si mettono "
     "scorze d'arancia candite o granella di pistacchio.",
     ["dolci", "ricotta"]),
    ("Cucina", "La pasta alla Norma",
     "Melanzane, pomodoro e ricotta salata.",
     "La pasta alla Norma è un piatto catanese: maccheroni con pomodoro fresco, melanzane "
     "fritte, basilico e ricotta salata grattugiata. Si dice che il nome sia un omaggio "
     "all'opera di Vincenzo Bellini, nato a Catania. È uno dei piatti più amati della cucina "
     "siciliana.",
     ["pasta", "melanzane"]),
    ("Cucina", "Granita e brioche, la colazione d'estate",
     "Limone, mandorla e gelsi neri.",
     "In Sicilia d'estate si fa colazione con la granita e la brioche col tuppo. I gusti "
     "più classici sono il limone e la mandorla, ma in stagione si trova anche quella di "
     "gelsi neri. La granita si mangia col cucchiaino, e la brioche si inzuppa.",
     ["colazione", "granita"]),
    ("Viaggi", "Salire sull'Etna",
     "Il vulcano attivo più alto d'Europa.",
     "L'Etna è il vulcano attivo più alto d'Europa e domina tutta la costa orientale della "
     "Sicilia. Si può salire in funivia e poi proseguire con un'escursione guidata verso i "
     "crateri sommitali, quando le condizioni lo permettono. Serve abbigliamento pesante "
     "anche d'estate.",
     ["etna", "vulcano", "escursioni"]),
    ("Viaggi", "Ortigia a piedi",
     "Un giorno nell'isola di Siracusa.",
     "Ortigia è la parte più antica di Siracusa, collegata alla terraferma da un ponte. Si "
     "visita a piedi: la fonte Aretusa, il Duomo costruito attorno a un tempio greco, il "
     "mercato e le stradine affacciate sul mare.",
     ["siracusa", "mare"]),
    ("Viaggi", "Le Gole dell'Alcantara",
     "Un canyon di basalto scavato dal fiume.",
     "Le Gole dell'Alcantara sono una stretta gola di basalto, formatasi da antiche colate "
     "di lava dell'Etna e poi scavata dal fiume. L'acqua è fredda anche in agosto, e nei "
     "punti più stretti si cammina con gli stivali da pescatore.",
     ["alcantara", "basalto", "escursioni"]),
    ("Viaggi", "Taormina e il teatro greco",
     "Una vista sull'Etna e sul mare.",
     "Il teatro antico di Taormina, costruito dai greci e rimaneggiato dai romani, offre un "
     "panorama sul mare Ionio e sull'Etna. D'estate ospita concerti e spettacoli, e la "
     "città è piena di vicoli e terrazze.",
     ["taormina", "teatro"]),
    ("Storia", "Sant'Agata e la festa di Catania",
     "Tre giorni di devozione e di folla.",
     "La festa di Sant'Agata, patrona di Catania, si celebra dal 3 al 5 febbraio ed è una "
     "delle feste religiose più partecipate. Lungo le vie della città sfilano le candelore, "
     "grandi strutture decorate portate a spalla dalle corporazioni, e i devoti in saio "
     "bianco trainano il fercolo con le reliquie.",
     ["sant'agata", "tradizioni"]),
    ("Storia", "Il terremoto del 1693",
     "La ricostruzione barocca della Sicilia orientale.",
     "Nel gennaio del 1693 un violento terremoto distrusse gran parte della Sicilia "
     "orientale. Catania e le città del Val di Noto furono ricostruite in pochi decenni in "
     "stile barocco, con piani urbanistici ampi e rettilinei. Il risultato è oggi "
     "patrimonio dell'umanità.",
     ["terremoto", "barocco"]),
    ("Storia", "La pietra lavica nell'architettura catanese",
     "Il nero della lava e il bianco del calcare.",
     "A Catania molti palazzi e chiese sono costruiti con la pietra lavica, nera, in "
     "contrasto con il calcare bianco usato per le decorazioni. È un materiale locale, "
     "reperito alle falde dell'Etna, e dà alla città il suo aspetto inconfondibile.",
     ["architettura", "etna", "lava"]),
    ("Storia", "Il castello Ursino",
     "La fortezza di Federico II.",
     "Il castello Ursino fu costruito da Federico II nel Duecento, in riva al mare. Nel "
     "1669 una colata di lava dell'Etna lo circondò, e la linea di costa si spostò: oggi il "
     "castello sorge all'interno della città e ospita un museo civico.",
     ["castello", "federico ii"]),
]


class Command(BaseCommand):
    help = "Crea categorie, articoli e commenti di esempio."

    def handle(self, *args, **opzioni):
        adesso = timezone.now()
        categorie = {}
        for i, (nome_categoria, titolo, sommario, testo, tags) in enumerate(ARTICOLI):
            if nome_categoria not in categorie:
                categorie[nome_categoria] = Categoria.objects.get_or_create(
                    nome=nome_categoria, defaults={"slug": slugify(nome_categoria)}
                )[0]
            Articolo.objects.get_or_create(
                slug=slugify(titolo),
                defaults={
                    "categoria": categorie[nome_categoria],
                    "titolo": titolo,
                    "sommario": sommario,
                    "testo": testo,
                    "tags": tags,
                    "pubblicato": True,
                    "pubblicato_il": adesso - timedelta(days=i),
                },
            )
        Articolo.objects.get_or_create(
            slug="bozza-non-ancora-pronta",
            defaults={
                "titolo": "Bozza non ancora pronta",
                "testo": "Questo articolo non è pubblicato e non deve comparire nell'elenco.",
            },
        )
        primo = Articolo.objects.get(slug=slugify(ARTICOLI[0][1]))
        if not primo.commenti.exists():
            Commento.objects.create(articolo=primo, autore="Turi", testo="Arancino, sempre.")
            Commento.objects.create(articolo=primo, autore="Rosa", testo="Io dico arancina.")
        self.stdout.write(self.style.SUCCESS(f"{Articolo.objects.count()} articoli presenti."))
