from django.contrib.postgres.search import Lexeme, SearchQuery, SearchRank
from django.db.models import F

from articoli.models import Articolo


def cerca(testo, tipo="websearch"):
    query = SearchQuery(testo, config="italian", search_type=tipo)
    return (
        Articolo.objects.filter(ricerca=query)
        .annotate(rango=SearchRank(F("ricerca"), query))
        .order_by("-rango", "-pk")
    )


def slugs(queryset):
    return [a.slug for a in queryset]


def test_lo_stemming_italiano_trova_le_forme_flesse(articoli):
    # il testo contiene "arancino", la ricerca usa il plurale
    assert "arancino" in slugs(cerca("arancine"))


def test_la_bozza_compare_nella_ricerca_grezza(articoli):
    # il filtro sulla pubblicazione spetta alla vista, non alla ricerca
    assert "bozza" in slugs(cerca("arancino"))


def test_il_titolo_pesa_piu_del_testo(articoli):
    # "Etna" è nel titolo di un articolo e solo nel testo dell'altro
    assert slugs(cerca("etna"))[:2] == ["etna", "viaggio"]


def test_operatore_di_esclusione(articoli):
    assert slugs(cerca("etna -funivia")) == ["viaggio"]


def test_frase_esatta(articoli):
    assert slugs(cerca('"palla di riso"')) == ["arancino"]


def test_stemmer_vulcano_e_vulcani_non_coincidono(articoli):
    assert "etna" in slugs(cerca("vulcano"))
    assert "etna" not in slugs(cerca("vulcani"))


def test_il_prefisso_risolve_il_limite_dello_stemmer(articoli):
    query = SearchQuery(Lexeme("vulc", prefix=True), config="italian", search_type="raw")
    assert slugs(Articolo.objects.filter(ricerca=query)) == ["etna"]


def test_la_ricerca_ordinata_e_deterministica(articoli):
    assert cerca("etna").totally_ordered is True
