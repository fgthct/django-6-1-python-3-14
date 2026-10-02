"""Le viste che i test precedenti non attraversavano: li ha scoperti la misura della copertura."""

import pytest
from django.urls import reverse

from documenti import servizi
from documenti.models import Accesso, Documento

from .conftest import client_di, file_di_testo


def test_dal_web_si_concede_e_si_revoca_l_accesso(doc, marta, giulia):
    c = client_di(marta)
    r = c.post(reverse("accesso", args=[doc.pk]), {"utente": giulia.pk, "livello": Accesso.Livello.LETTURA})
    assert r.status_code == 302 and Accesso.objects.filter(documento=doc, utente=giulia).exists()
    assert client_di(giulia).get(reverse("dettaglio", args=[doc.pk])).status_code == 200
    c.post(reverse("revoca", args=[doc.pk, giulia.pk]))
    assert not Accesso.objects.filter(documento=doc, utente=giulia).exists()
    assert client_di(giulia).get(reverse("dettaglio", args=[doc.pk])).status_code == 404


def test_dal_web_solo_il_proprietario_concede_l_accesso(doc, marta, luca, giulia):
    servizi.concedi_accesso(marta, doc, luca, Accesso.Livello.MODIFICA)
    r = client_di(luca).post(
        reverse("accesso", args=[doc.pk]), {"utente": giulia.pk, "livello": Accesso.Livello.LETTURA}
    )
    assert r.status_code == 403 and not Accesso.objects.filter(utente=giulia).exists()


def test_dal_web_si_carica_una_nuova_versione(doc, marta):
    c = client_di(marta)
    r = c.post(
        reverse("nuova_versione", args=[doc.pk]),
        {"file": file_di_testo("Testo corretto.", "ferie.txt"), "nota": "Correzione"},
    )
    assert r.status_code == 302
    doc = Documento.objects.get(pk=doc.pk)
    assert doc.versione_corrente.numero == 2 and doc.versione_corrente.nota == "Correzione"


def test_dal_web_senza_file_si_resta_alla_pagina_con_un_avviso(doc, marta):
    r = client_di(marta).post(reverse("nuova_versione", args=[doc.pk]), {"nota": "niente file"}, follow=True)
    assert "Scegli un file" in r.text and doc.versioni.count() == 1


def test_dal_web_si_annulla_la_revisione(doc, marta, luca):
    servizi.invia_in_revisione(marta, doc, [luca], "sequenza")
    r = client_di(marta).post(reverse("annulla", args=[doc.pk]), headers={"HX-Request": "true"})
    assert r.status_code == 200 and "Revisione annullata" in r.text
    assert Documento.objects.get(pk=doc.pk).stato == Documento.Stato.BOZZA


@pytest.mark.parametrize("url", ["cerca", "chiedi"])
def test_la_ricerca_e_le_domande_chiedono_l_accesso(client, url):
    assert client.get(reverse(url)).status_code in (302, 405)


def test_la_ricerca_dal_web_trova_solo_ci_che_si_puo_vedere(doc, marta, giulia, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        servizi.carica_versione(marta, doc, file_di_testo("Le ferie non godute decadono il trentuno marzo."))
    assert "Politica ferie" in client_di(marta).get(reverse("cerca"), {"q": "ferie non godute"}).text
    assert "Politica ferie" not in client_di(giulia).get(reverse("cerca"), {"q": "ferie non godute"}).text


def test_chiedere_senza_domanda_e_un_404(marta):
    assert client_di(marta).post(reverse("chiedi"), {"q": ""}).status_code == 404


def test_una_domanda_dal_web_senza_documenti_pertinenti_risponde_non_lo_so(marta):
    r = client_di(marta).post(reverse("chiedi"), {"q": "qualcosa di inesistente"})
    assert r.status_code == 200 and "Non ho trovato" in r.text
