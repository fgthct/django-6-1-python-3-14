import pytest
from django.test import Client
from django.urls import reverse

from assistenza import tenant
from assistenza.models import Commento, Ticket

from .conftest import client_web, crea_ticket

pytestmark = pytest.mark.django_db


def test_il_dominio_principale_mostra_la_pagina_pubblica(db):
    risposta = Client(HTTP_HOST="localhost").get("/")
    assert risposta.status_code == 200
    assert "Un helpdesk per ogni cliente" in risposta.text


def test_un_sottodominio_sconosciuto_e_404(db):
    assert Client(HTTP_HOST="fantasma.localhost").get("/").status_code == 404


def test_senza_accesso_si_va_al_login(acme):
    risposta = client_web(acme).get(reverse("dashboard"))
    assert risposta.status_code == 302
    assert risposta.url.startswith(reverse("login"))


def test_chi_non_e_membro_riceve_403(acme, rossi, admin_rossi):
    """Un utente valido per Rossi non entra da Acme, anche se la sessione fosse la stessa."""
    assert client_web(acme, admin_rossi).get(reverse("dashboard")).status_code == 403


def test_la_dashboard_mostra_solo_i_dati_del_tenant(acme, rossi, admin_acme, ticket_acme, ticket_rossi):
    testo = client_web(acme, admin_acme).get(reverse("dashboard")).text
    assert "Ticket di Acme" in testo
    assert "Ticket di Rossi" not in testo


def test_il_ticket_di_un_altro_tenant_e_404_non_403(acme, rossi, admin_acme, ticket_rossi):
    """403 direbbe «esiste, ma non per te»: già un'informazione. Per noi quel ticket non esiste."""
    risposta = client_web(acme, admin_acme).get(reverse("ticket", args=[ticket_rossi.pk]))
    assert risposta.status_code == 404


def test_htmx_riceve_solo_il_frammento(acme, admin_acme, ticket_acme):
    client = client_web(acme, admin_acme)
    pagina = client.get(reverse("dashboard")).text
    frammento = client.get(reverse("dashboard"), headers={"HX-Request": "true", "HX-Target": "elenco"}).text
    assert "<html" in pagina and "<html" not in frammento
    assert 'id="elenco"' in frammento and "Ticket di Acme" in frammento


def test_il_filtro_per_stato(acme, admin_acme):
    crea_ticket(acme, "Aperto uno")
    crea_ticket(acme, "Chiuso uno", stato=Ticket.Stato.CHIUSO)
    testo = client_web(acme, admin_acme).get(reverse("dashboard"), {"stato": "chiuso"}).text
    assert "Chiuso uno" in testo and "Aperto uno" not in testo


def test_i_contatori(acme, admin_acme):
    crea_ticket(acme, "a")
    crea_ticket(acme, "b")
    crea_ticket(acme, "c", stato=Ticket.Stato.CHIUSO)
    testo = client_web(acme, admin_acme).get(reverse("contatori")).text
    assert "<b>2</b> aperti" in testo and "<b>1</b> chiusi" in testo


def test_il_numero_di_query_non_dipende_dal_numero_di_ticket(acme, admin_acme, agente_acme,
                                                             django_assert_max_num_queries):
    """Con FETCH_RAISE un N+1 sarebbe un errore; qui verifichiamo anche che il conteggio non cresca."""
    with tenant.tenant(acme):
        for n in range(10):
            Ticket.objects.create(titolo=f"t{n}", richiedente="x@y.it", assegnato=agente_acme)
    client = client_web(acme, admin_acme)
    with django_assert_max_num_queries(8):
        risposta = client.get(reverse("dashboard"))
    assert risposta.status_code == 200
    assert "agente@acme.test" in risposta.text


def test_un_agente_commenta_e_riceve_il_frammento(acme, agente_acme, ticket_acme):
    client = client_web(acme, agente_acme)
    risposta = client.post(reverse("commenta", args=[ticket_acme.pk]), {"testo": "Ci lavoro io"})
    assert risposta.status_code == 200
    assert "Ci lavoro io" in risposta.text and "<html" not in risposta.text
    with tenant.tenant(acme):
        assert Commento.objects.count() == 1


def test_un_lettore_non_puo_commentare(acme, lettore_acme, ticket_acme):
    client = client_web(acme, lettore_acme)
    assert client.post(reverse("commenta", args=[ticket_acme.pk]), {"testo": "x"}).status_code == 403
    pagina = client.get(reverse("ticket", args=[ticket_acme.pk])).text
    assert "Commenta" not in pagina


def test_cambio_di_stato(acme, agente_acme, ticket_acme):
    risposta = client_web(acme, agente_acme).post(reverse("cambia_stato", args=[ticket_acme.pk]), {"stato": "chiuso"})
    assert risposta.status_code == 200
    with tenant.tenant(acme):
        assert Ticket.objects.get(pk=ticket_acme.pk).stato == "chiuso"


def test_un_post_senza_token_csrf_e_rifiutato(acme, agente_acme, ticket_acme):
    client = Client(HTTP_HOST="acme.localhost", enforce_csrf_checks=True)
    client.force_login(agente_acme.user)
    assert client.post(reverse("commenta", args=[ticket_acme.pk]), {"testo": "x"}).status_code == 403


def test_il_nuovo_ticket_via_form(acme, agente_acme):
    client = client_web(acme, agente_acme)
    risposta = client.post(reverse("nuovo"), {"titolo": "Stampante", "richiedente": "a@b.it", "priorita": 3})
    assert risposta.status_code == 302
    with tenant.tenant(acme):
        assert Ticket.objects.get().titolo == "Stampante"


def test_la_paginazione_della_dashboard(acme, admin_acme):
    for n in range(25):
        crea_ticket(acme, f"t{n:02d}")
    testo = client_web(acme, admin_acme).get(reverse("dashboard"), {"pagina": 3}).text
    assert "Pagina 3 di 3" in testo
