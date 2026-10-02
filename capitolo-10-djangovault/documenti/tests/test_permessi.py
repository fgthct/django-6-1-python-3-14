import pytest
from django.core.exceptions import PermissionDenied
from django.urls import reverse

from documenti import permessi, servizi
from documenti.models import Accesso, Documento

from .conftest import client_di

pytestmark = pytest.mark.django_db


def test_un_documento_e_visibile_al_proprietario_e_a_chi_ha_un_accesso(doc, marta, luca, giulia):
    servizi.concedi_accesso(marta, doc, luca, Accesso.Livello.LETTURA)
    assert list(Documento.objects.visibili_a(marta)) == [doc]
    assert list(Documento.objects.visibili_a(luca)) == [doc]
    assert list(Documento.objects.visibili_a(giulia)) == []


def test_i_livelli(doc, marta, luca, giulia, paolo):
    servizi.concedi_accesso(marta, doc, luca, Accesso.Livello.LETTURA)
    servizi.concedi_accesso(marta, doc, giulia, Accesso.Livello.MODIFICA)
    assert permessi.livello_di(marta, doc) == permessi.PROPRIETARIO
    assert permessi.livello_di(giulia, doc) == permessi.MODIFICA
    assert permessi.livello_di(luca, doc) == permessi.LETTURA
    assert permessi.livello_di(paolo, doc) == permessi.NESSUNO


def test_solo_il_proprietario_concede_accessi(doc, marta, luca, giulia):
    servizi.concedi_accesso(marta, doc, luca, Accesso.Livello.MODIFICA)
    with pytest.raises(PermissionDenied):
        servizi.concedi_accesso(luca, doc, giulia, Accesso.Livello.LETTURA)


def test_il_documento_degli_altri_non_esiste_nemmeno_per_nome(doc, giulia):
    """404, non 403: dire «esiste, ma non per te» è già un'informazione."""
    client = client_di(giulia)
    assert client.get(reverse("dettaglio", args=[doc.pk])).status_code == 404
    assert client.get(reverse("scarica", args=[doc.pk, 1])).status_code == 404
    assert client.post(reverse("annulla", args=[doc.pk])).status_code == 404


def test_l_elenco_mostra_solo_i_documenti_visibili(doc, marta, giulia):
    assert "Politica ferie" in client_di(marta).get(reverse("elenco")).text
    assert "Politica ferie" not in client_di(giulia).get(reverse("elenco")).text


def test_senza_accesso_si_va_al_login(doc, client):
    risposta = client.get(reverse("dettaglio", args=[doc.pk]))
    assert risposta.status_code == 302 and reverse("login") in risposta.url


def test_i_file_si_scaricano_solo_dalla_vista_con_i_permessi(doc, marta):
    assert client_di(marta).get("/media/" + doc.versione_corrente.file.name).status_code == 404
    risposta = client_di(marta).get(reverse("scarica", args=[doc.pk, 1]))
    assert risposta.status_code == 200
    assert b"Primo paragrafo" in b"".join(risposta.streaming_content)
    assert "attachment" in risposta["Content-Disposition"]


def test_un_lettore_non_puo_revocare_ne_concedere_dal_web(doc, marta, luca, giulia):
    servizi.concedi_accesso(marta, doc, luca, Accesso.Livello.LETTURA)
    risposta = client_di(luca).post(reverse("accesso", args=[doc.pk]), {"utente": giulia.pk, "livello": 1})
    assert risposta.status_code == 403
    assert not Accesso.objects.filter(utente=giulia).exists()


def test_l_elenco_ha_un_numero_costante_di_query(marta, django_assert_max_num_queries):
    from .conftest import file_di_testo
    for n in range(8):
        servizi.crea_documento(marta, f"Documento {n}", file_di_testo(f"testo {n}"))
    client = client_di(marta)
    with django_assert_max_num_queries(6):
        assert client.get(reverse("elenco")).status_code == 200
