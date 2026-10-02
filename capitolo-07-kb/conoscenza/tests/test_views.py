import pytest

pytestmark = pytest.mark.django_db


def test_indice(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b'hx-get="/cerca/"' in r.content
    assert b"Scrivi una domanda" not in r.content  # i partial non si vedono nella pagina intera


def test_cerca_restituisce_solo_il_frammento(client, corpus):
    r = client.get("/cerca/", {"q": "modulo RS-12"})
    assert r.status_code == 200
    assert b"<html" not in r.content
    assert b"Rimborsi spese" in r.content
    assert "per significato" in r.content.decode()


def test_cerca_senza_domanda(client):
    assert b"Scrivi una domanda" in client.get("/cerca/").content


def test_un_modo_sconosciuto_ricade_sull_ibrida(client, corpus):
    r = client.get("/cerca/", {"q": "RS-12", "modo": "inventato"})
    assert r.status_code == 200 and r.context["modo"] == "ibrida"


@pytest.mark.parametrize("modo", ["ibrida", "significato", "parole"])
def test_i_tre_modi(client, corpus, modo):
    r = client.get("/cerca/", {"q": "RS-12", "modo": modo})
    assert b"Rimborsi spese" in r.content


def test_il_testo_dei_documenti_e_escapato(client, corpus):
    from conoscenza.models import Chunk
    Chunk.objects.filter(testo__contains="RS-12").update(testo="<script>alert(1)</script> RS-12")
    r = client.get("/cerca/", {"q": "RS-12", "modo": "parole"})
    assert b"<script>alert" not in r.content
    assert b"&lt;script&gt;" in r.content


def test_chiedi(client, corpus):
    r = client.get("/chiedi/", {"q": "modulo RS-12 per il rimborso"})
    assert b"RS-12" in r.content and b"Fonti" in r.content


def test_chiedi_fuori_tema(client, corpus, settings):
    settings.RAG_DISTANZA_MASSIMA = 0.0
    assert b"nonso" in client.get("/chiedi/", {"q": "carbonara"}).content
