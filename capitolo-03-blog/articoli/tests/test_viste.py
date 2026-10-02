import pytest
from django.db import models
from django.urls import reverse

from articoli.models import Articolo, Commento

from .conftest import crea_articolo


def test_elenco_mostra_solo_gli_articoli_pubblicati(client, articoli):
    risposta = client.get(reverse("articoli:elenco"))
    titoli = [a.titolo for a in risposta.context["object_list"]]
    assert "Una bozza" not in titoli
    assert len(titoli) == 3


def test_elenco_dal_piu_recente(client, articoli):
    risposta = client.get(reverse("articoli:elenco"))
    assert [a.slug for a in risposta.context["object_list"]] == ["arancino", "etna", "viaggio"]


def test_ricerca_con_evidenziazione(client, articoli):
    risposta = client.get(reverse("articoli:elenco"), {"q": "arancine"})
    html = risposta.content.decode()
    assert "<mark>arancino</mark>" in html


def test_la_ricerca_non_mostra_le_bozze(client, articoli):
    risposta = client.get(reverse("articoli:elenco"), {"q": "arancino"})
    assert [a.slug for a in risposta.context["object_list"]] == ["arancino"]


def test_l_evidenziazione_non_permette_html_iniettato(client, db):
    # un tag non chiuso sopravvive a ts_headline: solo l'escape ci protegge
    crea_articolo("xss", "Titolo", "Testo con <img src=x onerror=alert(1) e la parola cannolo.")
    risposta = client.get(reverse("articoli:elenco"), {"q": "cannolo"})
    html = risposta.content.decode()
    assert "<img src=x" not in html
    assert "&lt;img src=x onerror=alert(1)" in html
    assert "<mark>cannolo</mark>" in html


def test_filtro_per_tag(client, articoli):
    risposta = client.get(reverse("articoli:elenco"), {"tag": "viaggi"})
    assert [a.slug for a in risposta.context["object_list"]] == ["viaggio"]


def test_filtro_per_categoria(client, articoli):
    risposta = client.get(reverse("articoli:elenco"), {"categoria": "cucina"})
    assert [a.slug for a in risposta.context["object_list"]] == ["arancino"]


def test_dettaglio_di_una_bozza_non_esiste(client, articoli):
    risposta = client.get(reverse("articoli:dettaglio", args=["bozza"]))
    assert risposta.status_code == 404


def test_commento(client, articoli):
    url = reverse("articoli:commenta", args=["etna"])
    risposta = client.post(url, {"autore": "Rosa", "testo": "Bellissimo"})
    assert risposta.status_code == 302
    assert Commento.objects.filter(articolo=articoli["etna"], autore="Rosa").exists()


def test_commento_su_una_bozza_e_rifiutato(client, articoli):
    url = reverse("articoli:commenta", args=["bozza"])
    assert client.post(url, {"autore": "Rosa", "testo": "x"}).status_code == 404


def test_elenco_ha_un_numero_fisso_di_query(client, articoli, django_assert_num_queries):
    with django_assert_num_queries(3):   # conteggio, pagina, categorie
        client.get(reverse("articoli:elenco"))


def test_la_paginazione_non_ripete_ne_perde_articoli(client, db):
    for i in range(14):
        crea_articolo(f"a{i}", f"Articolo {i}", "testo con la parola cannolo")
    visti = []
    for pagina in (1, 2, 3):
        risposta = client.get(reverse("articoli:elenco"), {"q": "cannolo", "page": pagina})
        visti += [a.pk for a in risposta.context["object_list"]]
    assert len(visti) == 14
    assert len(set(visti)) == 14
    assert set(visti) == set(Articolo.objects.values_list("pk", flat=True))


def test_l_elenco_con_ricerca_ha_un_ordinamento_deterministico(client, articoli):
    risposta = client.get(reverse("articoli:elenco"), {"q": "etna"})
    queryset = risposta.context["paginator"].object_list
    assert queryset.totally_ordered is True
