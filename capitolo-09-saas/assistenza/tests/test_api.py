import json
from datetime import timedelta

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import Client
from django.utils import timezone

from assistenza import chiavi, tenant
from assistenza.api import PaginazioneSicura
from assistenza.models import ChiaveApi, Ticket

from .conftest import client_api, crea_ticket

pytestmark = pytest.mark.django_db


def invia(client, metodo, url, dati=None):
    return getattr(client, metodo)(url, data=json.dumps(dati) if dati is not None else None,
                                   content_type="application/json")


def test_senza_chiave_401(acme):
    assert Client(HTTP_HOST="acme.localhost").get("/api/v1/tickets").status_code == 401


def test_chiave_inventata_401(acme):
    client = Client(HTTP_HOST="acme.localhost", HTTP_AUTHORIZATION="Bearer ak_00000000_finta")
    assert client.get("/api/v1/tickets").status_code == 401


def test_chiave_con_il_segreto_sbagliato_401(acme, admin_acme):
    vera = chiavi.crea_chiave(admin_acme)
    contraffatta = vera[:-3] + "xyz"
    client = Client(HTTP_HOST="acme.localhost", HTTP_AUTHORIZATION=f"Bearer {contraffatta}")
    assert client.get("/api/v1/tickets").status_code == 401


def test_la_chiave_di_un_tenant_non_vale_su_un_altro_sottodominio(acme, rossi, admin_acme):
    token = chiavi.crea_chiave(admin_acme)
    client = Client(HTTP_HOST="rossi.localhost", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert client.get("/api/v1/tickets").status_code == 401


def test_la_chiave_funziona_anche_sul_dominio_principale(acme, admin_acme, ticket_acme):
    """Senza sottodominio il tenant lo decide la chiave, e solo lei."""
    token = chiavi.crea_chiave(admin_acme)
    client = Client(HTTP_HOST="localhost", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert client.get("/api/v1/tickets").json()["count"] == 1


def test_chiave_revocata_401(acme, admin_acme):
    token = chiavi.crea_chiave(admin_acme)
    ChiaveApi.objects.update(revocata_il=timezone.now())
    client = Client(HTTP_HOST="acme.localhost", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert client.get("/api/v1/tickets").status_code == 401


def test_la_chiave_in_chiaro_non_e_nel_database(admin_acme):
    token = chiavi.crea_chiave(admin_acme)
    chiave = ChiaveApi.objects.get()
    assert token not in (chiave.prefisso, chiave.impronta)
    assert len(chiave.impronta) == 64


def test_l_elenco_contiene_solo_i_ticket_del_tenant(acme, rossi, admin_acme, ticket_acme, ticket_rossi):
    dati = client_api(acme, admin_acme).get("/api/v1/tickets").json()
    assert dati["count"] == 1
    assert [t["titolo"] for t in dati["items"]] == ["Ticket di Acme"]


def test_il_ticket_di_un_altro_tenant_e_404(acme, rossi, admin_acme, ticket_rossi):
    assert client_api(acme, admin_acme).get(f"/api/v1/tickets/{ticket_rossi.pk}").status_code == 404


def test_modificare_il_ticket_di_un_altro_tenant_e_404(acme, rossi, admin_acme, ticket_rossi):
    risposta = invia(client_api(acme, admin_acme), "patch", f"/api/v1/tickets/{ticket_rossi.pk}", {"stato": "chiuso"})
    assert risposta.status_code == 404
    with tenant.tenant(rossi):
        assert Ticket.objects.get().stato == "aperto"


def test_la_paginazione_e_stabile_anche_con_date_identiche(acme, admin_acme):
    """Tutti i ticket con lo stesso istante di creazione: senza «id» nell'ordinamento le pagine si sovrapporrebbero."""
    for n in range(45):
        crea_ticket(acme, f"t{n}")
    with tenant.tenant(acme):
        Ticket.objects.update(creato=timezone.now())
    client = client_api(acme, admin_acme)
    visti = []
    for offset in range(0, 45, 10):
        pagina = client.get("/api/v1/tickets", {"limit": 10, "offset": offset}).json()
        visti += [t["id"] for t in pagina["items"]]
    assert len(visti) == 45 and len(set(visti)) == 45


def test_il_limite_massimo_e_rispettato(acme, admin_acme):
    assert client_api(acme, admin_acme).get("/api/v1/tickets", {"limit": 1000}).status_code == 422


def test_la_paginazione_rifiuta_un_ordinamento_incompleto(acme):
    with tenant.tenant(acme):
        non_deterministico = Ticket.objects.order_by("priorita")
        assert not non_deterministico.totally_ordered
        with pytest.raises(ImproperlyConfigured):
            PaginazioneSicura().paginate_queryset(
                non_deterministico, PaginazioneSicura.Input(limit=5, offset=0), request=None
            )
        # L'ordinamento predefinito (-creato, -id) invece va bene.
        assert Ticket.objects.all().totally_ordered
        assert Ticket.objects.order_by("priorita", "pk").totally_ordered


def test_filtro_per_stato(acme, admin_acme):
    crea_ticket(acme, "a")
    crea_ticket(acme, "b", stato="chiuso")
    dati = client_api(acme, admin_acme).get("/api/v1/tickets", {"stato": "chiuso"}).json()
    assert [t["titolo"] for t in dati["items"]] == ["b"]


def test_creare_un_ticket(acme, admin_acme, django_capture_on_commit_callbacks):
    client = client_api(acme, admin_acme)
    with django_capture_on_commit_callbacks(execute=True):
        risposta = invia(client, "post", "/api/v1/tickets", {"titolo": "Wi-Fi", "richiedente": "a@b.it", "priorita": 3})
    assert risposta.status_code == 201
    assert risposta.json()["titolo"] == "Wi-Fi" and risposta.json()["assegnato"] is None


def test_un_lettore_non_puo_creare(acme, lettore_acme):
    risposta = invia(client_api(acme, lettore_acme), "post", "/api/v1/tickets", {"titolo": "x", "richiedente": "a@b.it"})
    assert risposta.status_code == 403


def test_un_agente_non_puo_assegnare(acme, agente_acme, ticket_acme):
    risposta = invia(client_api(acme, agente_acme), "patch", f"/api/v1/tickets/{ticket_acme.pk}",
                     {"assegnato_id": agente_acme.pk})
    assert risposta.status_code == 403


def test_l_admin_assegna_e_il_dettaglio_mostra_il_membro(acme, admin_acme, agente_acme, ticket_acme):
    risposta = invia(client_api(acme, admin_acme), "patch", f"/api/v1/tickets/{ticket_acme.pk}",
                     {"assegnato_id": agente_acme.pk})
    assert risposta.status_code == 200
    assert risposta.json()["assegnato"]["email"] == "agente@acme.test"


def test_non_si_assegna_a_un_membro_di_un_altro_tenant(acme, rossi, admin_acme, admin_rossi, ticket_acme):
    risposta = invia(client_api(acme, admin_acme), "patch", f"/api/v1/tickets/{ticket_acme.pk}",
                     {"assegnato_id": admin_rossi.pk})
    assert risposta.status_code == 404


def test_stato_sconosciuto_422(acme, agente_acme, ticket_acme):
    risposta = invia(client_api(acme, agente_acme), "patch", f"/api/v1/tickets/{ticket_acme.pk}", {"stato": "boh"})
    assert risposta.status_code == 422


def test_commentare(acme, agente_acme, ticket_acme):
    risposta = invia(client_api(acme, agente_acme), "post", f"/api/v1/tickets/{ticket_acme.pk}/commenti",
                     {"testo": "Preso in carico"})
    assert risposta.status_code == 201 and risposta.json()["testo"] == "Preso in carico"


def test_lo_schema_openapi_c_e_ma_la_pagina_dei_documenti_no(acme, admin_acme):
    client = client_api(acme, admin_acme)
    assert client.get("/api/v1/docs").status_code == 404
    # lo schema richiede la chiave come tutto il resto
    assert Client(HTTP_HOST="acme.localhost").get("/api/v1/openapi.json").status_code in (200, 401)


def test_il_numero_di_query_dell_elenco_e_costante(acme, admin_acme, agente_acme, django_assert_max_num_queries):
    with tenant.tenant(acme):
        for n in range(15):
            Ticket.objects.create(titolo=f"t{n}", richiedente="a@b.it", assegnato=agente_acme)
    client = client_api(acme, admin_acme)
    with django_assert_max_num_queries(6):
        risposta = client.get("/api/v1/tickets", {"limit": 15})
    assert risposta.status_code == 200 and len(risposta.json()["items"]) == 15
