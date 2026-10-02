import inspect

from django.urls import reverse

from vetrina import views

HTMX = {"HTTP_HX_REQUEST": "true"}


def test_la_vista_del_catalogo_e_davvero_asincrona():
    assert inspect.iscoroutinefunction(views.catalogo)


def test_pagina_intera_e_frammento(client, catalogo):
    intera = client.get(reverse("vetrina:catalogo"))
    frammento = client.get(reverse("vetrina:catalogo"), **HTMX)
    assert "<html" in intera.text and "<html" not in frammento.text
    assert "HX-Request" in frammento["Vary"]
    assert "Prodotto 00" in frammento.text


def test_la_paginazione_asincrona_divide_in_pagine(client, catalogo):
    p1 = client.get(reverse("vetrina:catalogo"), **HTMX)
    p3 = client.get(reverse("vetrina:catalogo"), {"pagina": 3}, **HTMX)
    assert "Prodotto 05" in p1.text and "Prodotto 06" not in p1.text
    assert "Prodotto 13" in p3.text and "Successiva" not in p3.text
    assert "14 prodotti" in p1.text


def test_pagina_fuori_intervallo_mostra_l_ultima(client, catalogo):
    r = client.get(reverse("vetrina:catalogo"), {"pagina": 99}, **HTMX)
    assert "Prodotto 13" in r.text


def test_i_filtri_si_combinano(client, catalogo):
    dolci = catalogo[0].categoria_id
    r = client.get(reverse("vetrina:catalogo"), {"categoria": dolci, "q": "prodotto 0"}, **HTMX)
    assert "Prodotto 00" in r.text and "Prodotto 01" not in r.text


def test_i_link_di_paginazione_funzionano_anche_senza_htmx(client, catalogo):
    r = client.get(reverse("vetrina:catalogo"))
    assert 'href="?q=&categoria=&pagina=2"' in r.text


def test_il_numero_di_query_non_dipende_dal_numero_di_prodotti(client, catalogo):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    with CaptureQueriesContext(connection) as a:
        client.get(reverse("vetrina:catalogo"), {"pagina": 1}, **HTMX)
    # con un solo prodotto nella pagina il numero deve essere identico
    with CaptureQueriesContext(connection) as b:
        client.get(reverse("vetrina:catalogo"), {"q": "Prodotto 00"}, **HTMX)
    assert len(a) == len(b)


def test_ordinamento_totale(db):
    from vetrina.models import Prodotto
    assert Prodotto.objects.all().totally_ordered


def test_un_visitatore_con_sessione_vede_il_suo_carrello_nel_catalogo(client, catalogo):
    # Il difetto "sessione letta in modo sincrono" si manifesta solo quando
    # la sessione esiste già: un visitatore nuovo non lo farebbe emergere.
    client.post(reverse("vetrina:aggiungi", args=[catalogo[0].pk]), **HTMX)
    r = client.get(reverse("vetrina:catalogo"))
    assert r.status_code == 200
