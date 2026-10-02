import json
import re

import pytest
from django.test import Client
from django.urls import reverse

from assistenza.models import ViolazioneCsp

from .conftest import client_web

pytestmark = pytest.mark.django_db


def direttive(intestazione):
    return {parte.split()[0]: parte.split()[1:] for parte in intestazione.split(";") if parte.strip()}


def test_la_politica_e_su_ogni_risposta(acme, admin_acme):
    risposta = client_web(acme, admin_acme).get(reverse("dashboard"))
    politica = direttive(risposta["Content-Security-Policy"])
    assert politica["default-src"] == ["'self'"]
    assert politica["object-src"] == ["'none'"]
    assert politica["frame-ancestors"] == ["'none'"]
    assert politica["report-uri"] == ["/csp-report/"]


def test_nessuna_direttiva_ammette_il_codice_in_linea(acme, admin_acme):
    risposta = client_web(acme, admin_acme).get(reverse("dashboard"))
    for nome, valori in direttive(risposta["Content-Security-Policy"]).items():
        assert "'unsafe-inline'" not in valori, nome
        assert "'unsafe-eval'" not in valori, nome


def test_il_nonce_cambia_a_ogni_richiesta_e_coincide_con_lo_script(acme, admin_acme):
    client = client_web(acme, admin_acme)
    nonce_visti = []
    for _ in range(2):
        risposta = client.get(reverse("dashboard"))
        nell_intestazione = re.search(r"script-src [^;]*'nonce-([^']+)'", risposta["Content-Security-Policy"]).group(1)
        nella_pagina = re.search(r'<script nonce="([^"]+)"', risposta.text).group(1)
        assert nell_intestazione == nella_pagina
        nonce_visti.append(nell_intestazione)
    assert nonce_visti[0] != nonce_visti[1]


def test_la_politica_candidata_e_solo_in_osservazione(acme, admin_acme):
    risposta = client_web(acme, admin_acme).get(reverse("dashboard"))
    assert "require-trusted-types-for" in risposta["Content-Security-Policy-Report-Only"]
    assert "require-trusted-types-for" not in risposta["Content-Security-Policy"]


def test_le_pagine_non_hanno_script_o_stili_in_linea_senza_nonce(acme, admin_acme, ticket_acme):
    client = client_web(acme, admin_acme)
    for url in [reverse("dashboard"), reverse("nuovo"), reverse("ticket", args=[ticket_acme.pk])]:
        pagina = client.get(url).text
        assert not re.search(r"<script(?![^>]*(nonce=|src=))", pagina), url
        assert "<style" not in pagina and " style=" not in pagina, url
        assert not re.search(r"\bon[a-z]+=", pagina), url  # niente onclick=...


def rapporto(client, corpo, **extra):
    return client.post("/csp-report/", data=json.dumps(corpo), content_type="application/csp-report", **extra)


def test_il_rapporto_viene_salvato(acme):
    corpo = {"csp-report": {"document-uri": "http://acme.localhost/dashboard/", "effective-directive": "script-src-elem",
                            "blocked-uri": "https://evil.example/x.js", "disposition": "enforce"}}
    assert rapporto(Client(HTTP_HOST="acme.localhost"), corpo).status_code == 204
    v = ViolazioneCsp.objects.get()
    assert (v.direttiva, v.risorsa_bloccata, v.host, v.solo_osservazione) == (
        "script-src-elem", "https://evil.example/x.js", "acme.localhost", False)


def test_il_formato_della_reporting_api(db):
    corpo = [{"type": "csp-violation", "body": {"effectiveDirective": "style-src-attr", "blockedURL": "inline",
                                                 "documentURL": "http://acme.localhost/", "disposition": "report"}}]
    assert rapporto(Client(HTTP_HOST="localhost"), corpo).status_code == 204
    v = ViolazioneCsp.objects.get()
    assert v.direttiva == "style-src-attr" and v.solo_osservazione is True


def test_il_rapporto_non_richiede_il_token_csrf(db):
    client = Client(HTTP_HOST="localhost", enforce_csrf_checks=True)
    assert rapporto(client, {"csp-report": {"effective-directive": "img-src"}}).status_code == 204


def test_rapporti_difettosi_o_enormi_sono_rifiutati(db):
    client = Client(HTTP_HOST="localhost")
    assert client.post("/csp-report/", data="non json", content_type="application/json").status_code == 400
    assert rapporto(client, {"csp-report": {"blocked-uri": "x" * 20_000}}).status_code == 413
    assert client.get("/csp-report/").status_code == 405
    assert ViolazioneCsp.objects.count() == 0


def test_i_campi_lunghi_vengono_troncati(db):
    rapporto(Client(HTTP_HOST="localhost"), {"csp-report": {"blocked-uri": "u" * 3000}})
    assert len(ViolazioneCsp.objects.get().risorsa_bloccata) == 500
