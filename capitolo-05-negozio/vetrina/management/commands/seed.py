from decimal import Decimal

from django.core.management.base import BaseCommand

from vetrina.models import Categoria, Prodotto

CATALOGO = {
    "Dispensa": [
        ("Pasta di Gragnano 500 g", "Trafilata al bronzo, essiccata lentamente.", "2.40", 40),
        ("Olio extravergine 750 ml", "Frantoio siciliano, spremitura a freddo.", "11.90", 25),
        ("Pomodori secchi sott'olio", "Barattolo da 280 g.", "4.50", 30),
        ("Pistacchio di Bronte 200 g", "Sgusciato, tostato piano.", "14.00", 3),
        ("Capperi di Pantelleria", "Sotto sale, 150 g.", "3.80", 50),
        ("Riso Carnaroli 1 kg", "Invecchiato un anno.", "4.20", 35),
    ],
    "Dolci": [
        ("Cassata siciliana", "Monoporzione, ricotta e pan di spagna.", "4.80", 12),
        ("Cannoli (6 pezzi)", "Scorze croccanti, ricotta a parte.", "9.00", 8),
        ("Biscotti al mandorla", "Sacchetto da 300 g.", "5.50", 20),
        ("Torrone di Caltanissetta", "Tavoletta da 200 g.", "4.10", 0),
        ("Marmellata di arance", "Arance di Ribera, 250 g.", "3.90", 28),
        ("Granita in vasetto (limone)", "Da scongelare e mescolare.", "3.20", 15),
    ],
    "Bevande": [
        ("Nero d'Avola 75 cl", "Rosso, annata recente.", "9.50", 24),
        ("Grillo 75 cl", "Bianco fresco e sapido.", "8.90", 18),
        ("Amaro siciliano 70 cl", "Erbe e scorze di agrumi.", "16.00", 10),
        ("Aranciata amara", "Cassa da 6 bottiglie.", "8.40", 22),
        ("Caffè in grani 500 g", "Miscela a tostatura media.", "7.20", 30),
        ("Succo di melagrana", "Bottiglia da 750 ml.", "5.60", 14),
    ],
    "Casa": [
        ("Tagliere in ulivo", "Fatto a mano.", "32.00", 5),
        ("Grembiule in lino", "Colore sabbia.", "19.00", 9),
        ("Set di ceramiche di Caltagirone", "Quattro tazzine dipinte.", "45.00", 4),
        ("Candela al bergamotto", "Cera vegetale.", "12.00", 16),
    ],
}


class Command(BaseCommand):
    help = "Crea categorie e prodotti di prova (idempotente)."

    def handle(self, *args, **opzioni):
        creati = 0
        for nome_categoria, prodotti in CATALOGO.items():
            categoria, _ = Categoria.objects.get_or_create(nome=nome_categoria)
            for nome, descrizione, prezzo, giacenza in prodotti:
                _, nuovo = Prodotto.objects.get_or_create(
                    categoria=categoria, nome=nome,
                    defaults={"descrizione": descrizione, "prezzo": Decimal(prezzo), "giacenza": giacenza},
                )
                creati += nuovo
        self.stdout.write(f"{creati} prodotti creati, {Prodotto.objects.count()} in totale.")
