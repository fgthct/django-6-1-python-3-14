import sys
import types

import pytest
from django.core.management import CommandError, call_command

from documenti import embedder
from documenti.chunking import spezza
from documenti.models import Documento


@pytest.mark.django_db
def test_crea_demo_e_ripetibile(settings):
    settings.DEBUG = True
    call_command("crea_demo")
    call_command("crea_demo")
    assert Documento.objects.count() == 2


@pytest.mark.django_db
def test_crea_demo_in_produzione_si_rifiuta(settings):
    settings.DEBUG = False
    with pytest.raises(CommandError, match="DEBUG=1"):
        call_command("crea_demo")
    assert Documento.objects.count() == 0


def test_un_paragrafo_enorme_viene_tagliato():
    passaggi = spezza("parola " * 300, massimo=100)
    assert len(passaggi) > 10 and all(len(p) <= 100 for p in passaggi)
    assert "".join(passaggi).replace(" ", "") == ("parola" * 300)


def test_paragrafi_brevi_si_uniscono_finche_ci_stanno():
    assert spezza("uno\n\ndue\n\ntre", massimo=100) == ["uno\n\ndue\n\ntre"]
    assert spezza("uno\n\ndue\n\ntre", massimo=8) == ["uno\n\ndue", "tre"]


def test_un_paragrafo_senza_spazi_si_taglia_alla_lunghezza_massima():
    assert spezza("x" * 25, massimo=10) == ["x" * 10, "x" * 10, "x" * 5]


class _FalsoModello:
    def __init__(self, nome, cache_dir):
        self.dimensioni = 768

    def embed(self, testi):
        class Vettore(list):
            def tolist(self):
                return list(self)

        return [Vettore([0.5] * self.dimensioni) for _ in testi]


def test_il_backend_vero_chiama_fastembed(settings, monkeypatch):
    settings.EMBEDDING_BACKEND = "fastembed"
    monkeypatch.setitem(sys.modules, "fastembed", types.SimpleNamespace(TextEmbedding=_FalsoModello))
    embedder._modello.cache_clear()
    try:
        assert len(embedder.incorpora(["ciao"])[0]) == 768
    finally:
        embedder._modello.cache_clear()


def test_un_modello_con_dimensioni_sbagliate_viene_scoperto_subito(settings, monkeypatch):
    settings.EMBEDDING_BACKEND = "fastembed"
    settings.EMBEDDING_DIMENSIONI = 1024
    monkeypatch.setitem(sys.modules, "fastembed", types.SimpleNamespace(TextEmbedding=_FalsoModello))
    embedder._modello.cache_clear()
    try:
        with pytest.raises(ValueError, match="768 dimensioni, ne servono 1024"):
            embedder.incorpora(["ciao"])
    finally:
        embedder._modello.cache_clear()


def test_il_testo_accumulato_viene_chiuso_prima_di_un_paragrafo_enorme():
    passaggi = spezza("breve\n\n" + "parola " * 50, massimo=100)
    assert passaggi[0] == "breve" and len(passaggi) > 3
