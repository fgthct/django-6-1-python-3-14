import pytest
from django.test import Client
from django.urls import reverse

from contatti.models import Contatto

HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def contatti(db):
    return [
        Contatto.objects.create(nome=f"Persona {i:02d}", email=f"p{i}@example.com", citta="Roma" if i % 2 else "Milano")
        for i in range(25)
    ]


def test_richiesta_normale_restituisce_pagina_intera(client, contatti):
    r = client.get(reverse("contatti:elenco"))
    assert "<html" in r.text and "<h1>" in r.text


def test_richiesta_htmx_restituisce_solo_il_frammento(client, contatti):
    r = client.get(reverse("contatti:elenco"), **HTMX)
    assert "<html" not in r.text and "<h1>" not in r.text
    assert "Persona 00" in r.text


def test_risposta_varia_su_hx_request(client, contatti):
    r = client.get(reverse("contatti:elenco"))
    assert "HX-Request" in r["Vary"]


def test_ripristino_cronologia_vuole_la_pagina_intera(client, contatti):
    r = client.get(reverse("contatti:elenco"), **HTMX, HTTP_HX_HISTORY_RESTORE_REQUEST="true")
    assert "<html" in r.text


def test_ricerca_filtra_per_citta(client, contatti):
    r = client.get(reverse("contatti:elenco"), {"q": "milano"}, **HTMX)
    assert "Persona 00" in r.text and "Persona 01" not in r.text


def test_paginazione_carica_altri(client, contatti):
    r1 = client.get(reverse("contatti:elenco"), **HTMX)
    assert "carica-altri" in r1.text and "Persona 10" not in r1.text
    r3 = client.get(reverse("contatti:elenco"), {"pagina": 3}, **HTMX)
    assert "Persona 24" in r3.text and "carica-altri" not in r3.text


def test_queryset_con_ordinamento_totale(db):
    assert Contatto.objects.all().totally_ordered


def test_modifica_valida_restituisce_la_riga(client, contatti):
    c = contatti[0]
    r = client.post(reverse("contatti:modifica", args=[c.pk]),
                    {"nome": "Nuovo", "email": c.email, "telefono": "", "citta": ""}, **HTMX)
    assert r.status_code == 200 and f'id="contatto-{c.pk}"' in r.text and "Nuovo" in r.text
    c.refresh_from_db()
    assert c.nome == "Nuovo"


def test_modifica_non_valida_resta_200_con_errori(client, contatti):
    c = contatti[0]
    r = client.post(reverse("contatti:modifica", args=[c.pk]),
                    {"nome": "X", "email": contatti[1].email}, **HTMX)
    # HTMX 2 non scambia mai le risposte 4xx: gli errori di form devono viaggiare con 200
    assert r.status_code == 200 and "errorlist" in r.text


def test_creazione_htmx_risponde_con_form_nuovo_riga_e_contatore_oob(client, db):
    r = client.post(reverse("contatti:nuovo"), {"nome": "Ada", "email": "ada@example.com"}, **HTMX)
    assert 'id="form-nuovo"' in r.text
    assert 'hx-swap-oob="afterbegin:#righe"' in r.text and "Ada" in r.text
    assert 'hx-swap-oob="true"' in r.text and "(1 contatti)" in r.text


def test_creazione_senza_htmx_fa_redirect(client, db):
    r = client.post(reverse("contatti:nuovo"), {"nome": "Ada", "email": "ada@example.com"})
    assert r.status_code == 302 and Contatto.objects.count() == 1


def test_creazione_non_valida_senza_htmx_mostra_pagina_intera(client, db):
    r = client.post(reverse("contatti:nuovo"), {"nome": "", "email": "x"})
    assert r.status_code == 200 and "<html" in r.text and "errorlist" in r.text


def test_eliminazione_emette_trigger_e_non_204(client, contatti):
    pk = contatti[0].pk
    r = client.delete(reverse("contatti:elimina", args=[pk]), **HTMX)
    assert r.status_code == 200  # 204 non scambia il DOM: la riga resterebbe
    assert r["HX-Trigger"] == "contattiCambiati"
    assert not Contatto.objects.filter(pk=pk).exists()


def test_eliminazione_solo_con_delete(client, contatti):
    r = client.get(reverse("contatti:elimina", args=[contatti[0].pk]))
    assert r.status_code == 405


def test_csrf_rifiuta_post_senza_token(contatti):
    c = Client(enforce_csrf_checks=True)
    r = c.delete(reverse("contatti:elimina", args=[contatti[0].pk]), **HTMX)
    assert r.status_code == 403


def test_csrf_accetta_il_token_nell_header(contatti):
    c = Client(enforce_csrf_checks=True)
    pagina = c.get(reverse("contatti:elenco"))
    token = pagina.cookies["csrftoken"].value
    r = c.delete(reverse("contatti:elimina", args=[contatti[0].pk]), **HTMX, HTTP_X_CSRFTOKEN=token)
    assert r.status_code == 200


def test_annulla_modifica_restituisce_la_riga_originale(client, contatti):
    c = contatti[0]
    r = client.get(reverse("contatti:riga", args=[c.pk]), **HTMX)
    assert f'id="contatto-{c.pk}"' in r.text and c.nome in r.text and "<form" not in r.text
