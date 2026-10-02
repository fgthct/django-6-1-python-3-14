import pytest
from django.conf import settings

from frasi.models import Frase


def vettore(*valori):
    """Un vettore della dimensione giusta, con i primi valori dati e il resto a zero."""
    return list(valori) + [0.0] * (settings.EMBEDDING_DIMENSIONI - len(valori))


@pytest.fixture
def frasi_a_mano(db):
    """Tre frasi con vettori scelti da noi: il test non dipende da nessun modello."""
    return {
        "a": Frase.objects.create(testo="a: stessa direzione, corto", argomento="t", embedding=vettore(0.5, 0)),
        "b": Frase.objects.create(testo="b: lunghissimo e storto", argomento="t", embedding=vettore(10, 2)),
        "c": Frase.objects.create(testo="c: quasi uguale", argomento="t", embedding=vettore(0.9, 0.1)),
    }
