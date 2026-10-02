from django.contrib.postgres.search import SearchQuery
from django.db.models import JSONNull

from articoli.models import Articolo

from .conftest import crea_articolo


def test_str(articoli):
    assert str(articoli["etna"]) == "Salire sull'Etna"


def test_tags_sono_una_lista(articoli):
    articoli["arancino"].refresh_from_db()
    assert articoli["arancino"].tags == ["street food"]


def test_ordinamento_predefinito_e_deterministico(db):
    assert Articolo.objects.all().totally_ordered is True


def test_il_vettore_di_ricerca_si_aggiorna_da_solo(articoli):
    etna = articoli["etna"]
    query = SearchQuery("pistacchio", config="italian")
    assert not Articolo.objects.filter(ricerca=query).exists()
    etna.testo = "Un viaggio tra i pistacchi."
    etna.save()
    assert Articolo.objects.filter(ricerca=query).exists()


def test_json_null_e_null_sql_sono_diversi(db):
    a = crea_articolo("a", "A", "x", metadati=None)
    b = crea_articolo("b", "B", "x", metadati=JSONNull())
    solo_sql = Articolo.objects.filter(metadati__isnull=True)
    solo_json = Articolo.objects.filter(metadati=JSONNull())
    assert list(solo_sql) == [a]
    assert list(solo_json) == [b]
