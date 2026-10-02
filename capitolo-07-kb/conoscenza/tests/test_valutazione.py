import pytest

from conoscenza.valutazione import DOMANDE, Domanda, posizione_della_risposta, valuta


class C:
    def __init__(self, testo):
        self.testo = testo


D = Domanda("q", "risposta giusta", "esatta")


def test_posizione():
    assert posizione_della_risposta(D, [C("no"), C("ecco la risposta giusta")]) == 2
    assert posizione_della_risposta(D, [C("no")]) is None
    assert posizione_della_risposta(D, []) is None


def test_metriche():
    def strategia(q):
        return {"a": [C("risposta giusta")], "b": [C("x"), C("y"), C("risposta giusta")], "c": [C("x")]}[q]

    domande = [Domanda(q, "risposta giusta", "esatta") for q in "abc"]
    p = valuta(strategia, domande)
    assert p.hit_1 == pytest.approx(1 / 3)
    assert p.hit_3 == pytest.approx(2 / 3)
    assert p.mrr == pytest.approx((1 + 1 / 3 + 0) / 3)


def test_ogni_risposta_attesa_esiste_davvero_nei_documenti(corpus):
    """L'insieme d'oro non deve mentire: ogni frase attesa è in qualche chunk."""
    from conoscenza.models import Chunk
    for d in DOMANDE:
        assert Chunk.objects.filter(testo__contains=d.deve_contenere).exists(), d.testo
