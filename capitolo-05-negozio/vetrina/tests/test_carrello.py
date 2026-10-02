import json

import pytest
from django.test import Client
from django.urls import reverse

from vetrina.models import Ordine, Prodotto

HTMX = {"HTTP_HX_REQUEST": "true"}


def aggiungi(client, prodotto, **extra):
    return client.post(reverse("vetrina:aggiungi", args=[prodotto.pk]), **HTMX, **extra)


def test_aggiungi_aggiorna_il_badge_e_invia_un_messaggio(client, catalogo):
    r = aggiungi(client, catalogo[0])
    assert "Carrello (1)" in r.text and "<html" not in r.text
    evento = json.loads(r["HX-Trigger"])
    assert "aggiunto" in evento["messaggio"]["testo"]


def test_non_si_supera_la_giacenza(client, catalogo):
    for _ in range(5):
        aggiungi(client, catalogo[0])
    r = aggiungi(client, catalogo[0])
    assert "Carrello (5)" in r.text
    assert "non è più disponibile" in json.loads(r["HX-Trigger"])["messaggio"]["testo"]


def test_un_prodotto_esaurito_non_si_aggiunge(client, esaurito):
    r = aggiungi(client, esaurito)
    assert "Carrello (0)" in r.text


def test_imposta_limita_alla_giacenza_e_segnala_l_errore(client, catalogo):
    aggiungi(client, catalogo[0])
    r = client.post(reverse("vetrina:imposta", args=[catalogo[0].pk]), {"quantita": 50}, **HTMX)
    assert r.status_code == 200  # HTMX non sostituisce le risposte 4xx
    assert "ne restano solo 5" in r.text and "Carrello (5)" in r.text


def test_quantita_non_valida_e_un_errore_visibile_con_200(client, catalogo):
    r = client.post(reverse("vetrina:imposta", args=[catalogo[0].pk]), {"quantita": "abc"}, **HTMX)
    assert r.status_code == 200 and "Quantità non valida" in r.text


def test_quantita_zero_rimuove_la_riga(client, catalogo):
    aggiungi(client, catalogo[0])
    r = client.post(reverse("vetrina:imposta", args=[catalogo[0].pk]), {"quantita": 0}, **HTMX)
    assert "Il carrello è vuoto" in r.text and "Carrello (0)" in r.text


def test_il_totale_usa_i_prezzi_del_database(client, catalogo):
    aggiungi(client, catalogo[1]); aggiungi(client, catalogo[1])
    r = client.get(reverse("vetrina:carrello"))
    # il prezzo del prodotto 01 è 3.50: il totale è 7,00
    assert "€ 7,00" in r.text


def test_il_carrello_ignora_prodotti_spariti(client, catalogo):
    aggiungi(client, catalogo[0])
    Prodotto.objects.filter(pk=catalogo[0].pk).delete()
    r = client.get(reverse("vetrina:carrello"))
    assert r.status_code == 200 and "Il carrello è vuoto" in r.text


def test_ordine_riuscito(client, catalogo):
    aggiungi(client, catalogo[0]); aggiungi(client, catalogo[0]); aggiungi(client, catalogo[1])
    r = client.post(reverse("vetrina:ordina"), {"email": "a@example.com"}, **HTMX)
    ordine = Ordine.objects.get()
    assert r["HX-Redirect"] == reverse("vetrina:grazie", args=[ordine.pk])
    assert [(x.quantita, str(x.prezzo_unitario)) for x in ordine.righe.order_by("prodotto__nome")] == [(2, "2.50"), (1, "3.50")]
    catalogo[0].refresh_from_db()
    assert catalogo[0].giacenza == 3
    assert client.session.get("carrello") is None


def test_il_prezzo_dell_ordine_resta_anche_se_il_listino_cambia(client, catalogo):
    aggiungi(client, catalogo[0])
    client.post(reverse("vetrina:ordina"), {"email": "a@example.com"}, **HTMX)
    catalogo[0].prezzo = 99
    catalogo[0].save()
    assert str(Ordine.objects.get().righe.get().prezzo_unitario) == "2.50"


def test_ordine_senza_htmx_fa_redirect(client, catalogo):
    aggiungi(client, catalogo[0])
    r = client.post(reverse("vetrina:ordina"), {"email": "a@example.com"})
    assert r.status_code == 302


def test_ordine_atomico_se_una_riga_non_e_disponibile(client, catalogo):
    aggiungi(client, catalogo[0]); aggiungi(client, catalogo[1]); aggiungi(client, catalogo[1])
    # nel frattempo un altro cliente compra quasi tutto il secondo prodotto
    Prodotto.objects.filter(pk=catalogo[1].pk).update(giacenza=1)
    r = client.post(reverse("vetrina:ordina"), {"email": "a@example.com"}, **HTMX)
    assert r.status_code == 200 and "non è più disponibile" in r.text
    assert Ordine.objects.count() == 0
    catalogo[0].refresh_from_db()
    assert catalogo[0].giacenza == 5  # la prima riga, già scalata, è tornata indietro
    assert client.session["carrello"]  # il carrello non si perde


def test_ordine_con_carrello_vuoto(client, catalogo):
    r = client.post(reverse("vetrina:ordina"), {"email": "a@example.com"}, **HTMX)
    assert "Il carrello è vuoto" in r.text and Ordine.objects.count() == 0


def test_ordine_con_email_non_valida(client, catalogo):
    aggiungi(client, catalogo[0])
    r = client.post(reverse("vetrina:ordina"), {"email": "no"}, **HTMX)
    assert r.status_code == 200 and "errorlist" in r.text and Ordine.objects.count() == 0


def test_le_modifiche_richiedono_il_token_csrf(catalogo):
    c = Client(enforce_csrf_checks=True)
    r = c.post(reverse("vetrina:aggiungi", args=[catalogo[0].pk]), **HTMX)
    assert r.status_code == 403
    token = c.get(reverse("vetrina:catalogo")).cookies["csrftoken"].value
    r = c.post(reverse("vetrina:aggiungi", args=[catalogo[0].pk]), **HTMX, HTTP_X_CSRFTOKEN=token)
    assert r.status_code == 200
