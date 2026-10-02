import pytest

from campagne.models import Campagna, Consegna, Contatto
from campagne.tasks import prepara_consegne

pytestmark = pytest.mark.django_db


def test_crea_una_bozza(client):
    r = client.post("/", {"oggetto": "Ciao", "corpo": "Testo {nome}"})
    c = Campagna.objects.get()
    assert r.status_code == 302 and c.stato == Campagna.Stato.BOZZA


def test_avvia_accoda_una_volta_sola_anche_se_premuto_due_volte(client, campagna, coda_finta, django_capture_on_commit_callbacks):
    campagna.stato = Campagna.Stato.BOZZA
    campagna.save()
    with django_capture_on_commit_callbacks(execute=True):
        client.post(f"/campagne/{campagna.pk}/avvia/")
        client.post(f"/campagne/{campagna.pk}/avvia/")
    campagna.refresh_from_db()
    assert campagna.stato == Campagna.Stato.IN_INVIO
    assert len(coda_finta.results) == 1
    assert coda_finta.results[0].task.func is prepara_consegne.func


def test_avvia_vuole_post(client, campagna):
    assert client.get(f"/campagne/{campagna.pk}/avvia/").status_code == 405


def test_l_accodamento_aspetta_il_commit(client, campagna, coda_finta):
    campagna.stato = Campagna.Stato.BOZZA
    campagna.save()
    client.post(f"/campagne/{campagna.pk}/avvia/")  # nessuna cattura dei callback: il commit non c'è stato
    assert coda_finta.results == []


def _con_consegne(campagna, stati):
    for i, stato in enumerate(stati):
        c = Contatto.objects.create(email=f"u{i}@example.com", nome="U")
        Consegna.objects.create(campagna=campagna, contatto=c, stato=stato)


def test_l_avanzamento_calcola_la_percentuale(client, campagna):
    S = Consegna.Stato
    _con_consegne(campagna, [S.INVIATA, S.INVIATA, S.FALLITA, S.IN_ATTESA])
    r = client.get(f"/campagne/{campagna.pk}/avanzamento/")
    assert r.context["conteggi"] == {"totale": 4, "inviate": 2, "fallite": 1, "in_attesa": 1, "percentuale": 75}
    assert b"<html" not in r.content


def test_il_polling_continua_solo_finche_la_campagna_e_in_invio(client, campagna):
    assert b'hx-trigger="every 2s"' in client.get(f"/campagne/{campagna.pk}/avanzamento/").content
    campagna.stato = Campagna.Stato.COMPLETATA
    campagna.save()
    assert b"hx-trigger" not in client.get(f"/campagne/{campagna.pk}/avanzamento/").content


def test_il_dettaglio_mostra_il_pulsante_solo_per_una_bozza(client, campagna):
    assert b"Avvia l" not in client.get(f"/campagne/{campagna.pk}/").content
    campagna.stato = Campagna.Stato.BOZZA
    campagna.save()
    assert b"Avvia l" in client.get(f"/campagne/{campagna.pk}/").content


def test_campagna_inesistente(client):
    assert client.get("/campagne/999/").status_code == 404
