"""Le regole di progetto, verificate: fetch mode, contesto del tenant, servizi."""

import pytest
from django.core.exceptions import ValidationError
from django.core.exceptions import FieldFetchBlocked
from django.urls import reverse

from assistenza import servizi, tenant
from assistenza.models import Ticket

from .conftest import client_web

pytestmark = pytest.mark.django_db


def test_nei_test_una_query_nascosta_e_un_errore(acme, agente_acme):
    with tenant.tenant(acme):
        Ticket.objects.create(titolo="x", richiedente="a@b.it", assegnato=agente_acme)
        ticket = Ticket.objects.get()
        with pytest.raises(FieldFetchBlocked):
            ticket.assegnato


def test_in_produzione_la_stessa_query_diventa_una_sola(acme, agente_acme, settings, django_assert_num_queries):
    settings.MODALITA_FETCH = "FETCH_PEERS"
    with tenant.tenant(acme):
        for n in range(5):
            Ticket.objects.create(titolo=f"t{n}", richiedente="a@b.it", assegnato=agente_acme)
        with django_assert_num_queries(2):
            for ticket in Ticket.objects.all():
                ticket.assegnato


def test_dopo_una_richiesta_nessun_tenant_resta_attivo(acme, admin_acme):
    risposta = client_web(acme, admin_acme).get(reverse("dashboard"))
    assert risposta.status_code == 200
    assert tenant.corrente_o_nessuno() is None


def test_il_servizio_rifiuta_un_destinatario_di_un_altro_tenant(acme, rossi, admin_acme, admin_rossi, ticket_acme):
    with tenant.tenant(acme):
        with pytest.raises(ValidationError):
            servizi.assegna(admin_acme, ticket_acme, admin_rossi)


def test_sul_sottodominio_la_radice_porta_alla_dashboard(acme, admin_acme):
    risposta = client_web(acme, admin_acme).get("/")
    assert risposta.status_code == 302 and risposta.url == reverse("dashboard")
