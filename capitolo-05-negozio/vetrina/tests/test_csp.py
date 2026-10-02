import re

from django.urls import reverse


def test_la_pagina_porta_una_csp_con_nonce(client, catalogo):
    r = client.get(reverse("vetrina:catalogo"))
    politica = r["Content-Security-Policy"]
    nonce = re.search(r"'nonce-([^']+)'", politica).group(1)
    assert f'<script nonce="{nonce}">' in r.text


def test_il_nonce_cambia_a_ogni_risposta(client, catalogo):
    a = client.get(reverse("vetrina:catalogo"))["Content-Security-Policy"]
    b = client.get(reverse("vetrina:catalogo"))["Content-Security-Policy"]
    assert a != b


def test_la_politica_non_ammette_codice_o_stili_inline(client, catalogo):
    politica = client.get(reverse("vetrina:catalogo"))["Content-Security-Policy"]
    assert "'unsafe-inline'" not in politica and "'unsafe-eval'" not in politica
    assert "default-src 'none'" in politica


def test_le_pagine_non_hanno_stili_ne_gestori_inline(client, catalogo):
    for url in (reverse("vetrina:catalogo"), reverse("vetrina:carrello")):
        html = client.get(url).text
        assert "<style" not in html
        assert not re.search(r"\son[a-z]+=", html)   # onclick=, onchange=, ...
        assert " style=" not in html
