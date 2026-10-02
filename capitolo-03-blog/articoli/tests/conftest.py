from datetime import timedelta

import pytest
from django.utils import timezone

from articoli.models import Articolo, Categoria


@pytest.fixture
def categoria(db):
    return Categoria.objects.create(nome="Cucina", slug="cucina")


def crea_articolo(slug, titolo, testo, **extra):
    extra.setdefault("pubblicato", True)
    extra.setdefault("pubblicato_il", timezone.now())
    return Articolo.objects.create(slug=slug, titolo=titolo, testo=testo, **extra)


@pytest.fixture
def articoli(categoria):
    adesso = timezone.now()
    return {
        "arancino": crea_articolo(
            "arancino", "Il grande dibattito",
            "Un arancino è una palla di riso fritta.",
            categoria=categoria, tags=["street food"],
            pubblicato_il=adesso - timedelta(days=1),
        ),
        "etna": crea_articolo(
            "etna", "Salire sull'Etna",
            "Il vulcano si sale in funivia.",
            pubblicato_il=adesso - timedelta(days=2),
        ),
        "viaggio": crea_articolo(
            "viaggio", "Un viaggio in Sicilia",
            "Tra le tappe c'è anche l'Etna, con una bella escursione.",
            tags=["viaggi"], pubblicato_il=adesso - timedelta(days=3),
        ),
        "bozza": crea_articolo(
            "bozza", "Una bozza", "Nessuno deve leggere questo arancino.",
            pubblicato=False, pubblicato_il=None,
        ),
    }
