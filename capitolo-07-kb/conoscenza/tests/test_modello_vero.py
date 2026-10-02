"""Prova con il modello vero. Lenta e pesante: si esegue solo su richiesta.

    KB_MODELLO_VERO=1 uv run pytest -m modello_vero
"""
import os

import pytest

from conoscenza import ricerca, valutazione

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.modello_vero,
    pytest.mark.skipif(not os.environ.get("KB_MODELLO_VERO"), reason="KB_MODELLO_VERO non impostata"),
]


def test_la_ricerca_ibrida_non_peggiora(corpus):
    """Una rete di sicurezza: se cambiate modello o chunking e questo crolla, lo saprete."""
    p = valutazione.valuta(lambda q: [r.chunk for r in ricerca.cerca_ibrida(q, 10)])
    assert p.hit_3 >= 0.9
    assert p.mrr >= 0.85
