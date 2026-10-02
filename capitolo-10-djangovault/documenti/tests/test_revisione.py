import threading

import pytest
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, connections, transaction
from django.urls import reverse

from documenti import servizi
from documenti.models import Accesso, Documento, Partecipante, Revisione
from documenti.servizi import ErroreDiDominio

from .conftest import client_di, file_di_testo

pytestmark = pytest.mark.django_db
SEQ, LIB = Revisione.Modalita.IN_SEQUENZA, Revisione.Modalita.LIBERA


def test_solo_il_proprietario_sceglie_i_revisori(doc, marta, luca, giulia):
    servizi.concedi_accesso(marta, doc, luca, Accesso.Livello.MODIFICA)
    with pytest.raises(PermissionDenied):
        servizi.invia_in_revisione(luca, doc, [giulia], SEQ)  # nemmeno chi può modificare
    doc.refresh_from_db()
    assert doc.stato == Documento.Stato.BOZZA


@pytest.mark.parametrize("scelta, messaggio", [
    ("nessuno", "almeno un revisore"), ("doppio", "due volte"), ("proprietario", "tuoi documenti"),
    ("troppi", "Al massimo"),
])
def test_scelte_di_revisori_non_valide(doc, marta, luca, giulia, paolo, scelta, messaggio):
    from .conftest import utente
    revisori = {"nessuno": [], "doppio": [luca, luca], "proprietario": [marta],
                "troppi": [luca, giulia, paolo] + [utente(f"u{n}") for n in range(4)]}[scelta]
    with pytest.raises(ErroreDiDominio, match=messaggio):
        servizi.invia_in_revisione(marta, doc, revisori, SEQ)


def test_inviare_in_revisione_da_accesso_in_lettura_ai_revisori(doc, marta, luca, giulia):
    servizi.invia_in_revisione(marta, doc, [luca, giulia], SEQ)
    assert Accesso.objects.filter(documento=doc).count() == 2
    doc.refresh_from_db()
    assert doc.stato == Documento.Stato.IN_REVISIONE


def test_non_si_invia_due_volte(doc, marta, luca):
    servizi.invia_in_revisione(marta, doc, [luca], SEQ)
    with pytest.raises(ErroreDiDominio, match="bozza"):
        servizi.invia_in_revisione(marta, doc, [luca], SEQ)


def test_in_sequenza_si_decide_nell_ordine(doc, marta, luca, giulia, paolo):
    servizi.invia_in_revisione(marta, doc, [luca, giulia, paolo], SEQ)
    with pytest.raises(ErroreDiDominio, match="turno"):
        servizi.decidi(giulia, doc, True)
    servizi.decidi(luca, doc, True)
    with pytest.raises(ErroreDiDominio, match="turno"):
        servizi.decidi(paolo, doc, True)
    servizi.decidi(giulia, doc, True)
    doc.refresh_from_db()
    assert doc.stato == Documento.Stato.IN_REVISIONE  # manca ancora Paolo
    servizi.decidi(paolo, doc, True)
    doc.refresh_from_db()
    assert doc.stato == Documento.Stato.APPROVATO
    assert doc.revisioni.get().stato == Revisione.Stato.APPROVATA


def test_chi_non_e_revisore_non_decide(doc, marta, luca, giulia):
    servizi.invia_in_revisione(marta, doc, [luca], SEQ)
    with pytest.raises(PermissionDenied):
        servizi.decidi(giulia, doc, True)
    with pytest.raises(PermissionDenied):
        servizi.decidi(marta, doc, True)  # nemmeno il proprietario approva da sé


def test_rimandare_riporta_in_bozza_e_serve_un_commento(doc, marta, luca, giulia):
    servizi.invia_in_revisione(marta, doc, [luca, giulia], SEQ)
    with pytest.raises(ErroreDiDominio, match="commento"):
        servizi.decidi(luca, doc, False, "   ")
    servizi.decidi(luca, doc, False, "Manca il capitolo tre")
    doc.refresh_from_db()
    assert doc.stato == Documento.Stato.BOZZA
    revisione = doc.revisioni.get()
    assert revisione.stato == Revisione.Stato.RIMANDATA
    assert revisione.partecipanti.get(utente=giulia).decisione == Partecipante.Decisione.SUPERATO
    servizi.invia_in_revisione(marta, doc, [luca], SEQ)  # si può ripartire


def test_in_modalita_libera_decide_chi_arriva_prima(doc, marta, luca, giulia, paolo):
    servizi.invia_in_revisione(marta, doc, [luca, giulia, paolo], LIB)
    servizi.decidi(paolo, doc, True)  # non è il primo della lista, e non importa
    doc.refresh_from_db()
    assert doc.stato == Documento.Stato.APPROVATO
    stati = {p.utente.username: p.decisione for p in doc.revisioni.get().partecipanti.all()}
    assert stati == {"luca": "superato", "giulia": "superato", "paolo": "approvato"}
    with pytest.raises(ErroreDiDominio, match="già stata conclusa"):
        servizi.decidi(luca, doc, True)


def test_non_si_decide_due_volte(doc, marta, luca, giulia):
    servizi.invia_in_revisione(marta, doc, [luca, giulia], SEQ)
    servizi.decidi(luca, doc, True)
    with pytest.raises(ErroreDiDominio, match="già deciso"):
        servizi.decidi(luca, doc, True)


def test_annullare_la_revisione(doc, marta, luca):
    servizi.invia_in_revisione(marta, doc, [luca], SEQ)
    with pytest.raises(PermissionDenied):
        servizi.annulla_revisione(luca, doc)
    servizi.annulla_revisione(marta, doc)
    doc.refresh_from_db()
    assert doc.stato == Documento.Stato.BOZZA and doc.revisioni.get().stato == Revisione.Stato.ANNULLATA


def test_durante_la_revisione_non_si_carica_e_non_si_toglie_un_revisore(doc, marta, luca):
    servizi.invia_in_revisione(marta, doc, [luca], SEQ)
    with pytest.raises(ErroreDiDominio, match="in revisione"):
        servizi.carica_versione(marta, doc, file_di_testo("Di nascosto"))
    with pytest.raises(ErroreDiDominio, match="revisore"):
        servizi.revoca_accesso(marta, doc, luca)


def test_il_database_non_ammette_due_revisioni_aperte(doc, marta, luca):
    servizi.invia_in_revisione(marta, doc, [luca], SEQ)
    with pytest.raises(IntegrityError), transaction.atomic():
        Revisione.objects.create(documento=doc, versione=doc.versione_corrente, modalita=SEQ)


def test_la_revisione_resta_legata_alla_versione_inviata(doc, marta, luca):
    servizi.invia_in_revisione(marta, doc, [luca], SEQ)
    assert doc.revisioni.get().versione == doc.versione_corrente


# --- notifiche -----------------------------------------------------------------------------------

def test_in_sequenza_si_avvisa_uno_alla_volta(doc, marta, luca, giulia, mailoutbox, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        servizi.invia_in_revisione(marta, doc, [luca, giulia], SEQ, "Controlla il capitolo 2")
    assert [m.to for m in mailoutbox] == [["luca@esempio.test"]]
    assert "Controlla il capitolo 2" in mailoutbox[0].body
    with django_capture_on_commit_callbacks(execute=True):
        servizi.decidi(luca, doc, True)
    assert [m.to for m in mailoutbox][1:] == [["giulia@esempio.test"]]
    with django_capture_on_commit_callbacks(execute=True):
        servizi.decidi(giulia, doc, True)
    assert mailoutbox[-1].to == ["marta@esempio.test"] and "Approvato" in mailoutbox[-1].subject


def test_in_modalita_libera_si_avvisano_tutti_con_messaggi_separati(doc, marta, luca, giulia, mailoutbox,
                                                                    django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        servizi.invia_in_revisione(marta, doc, [luca, giulia], LIB, "Se avete qualcosa da aggiungere…")
    assert sorted(m.to[0] for m in mailoutbox) == ["giulia@esempio.test", "luca@esempio.test"]
    assert all(len(m.to) == 1 for m in mailoutbox)  # nessuno vede gli altri destinatari


def test_nessuna_notifica_se_la_transazione_fallisce(doc, marta, luca, mailoutbox, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        servizi.invia_in_revisione(marta, doc, [luca], SEQ)
    assert mailoutbox == [] and len(callbacks) == 1  # parte soltanto quando si fa il commit


def test_il_rimando_avvisa_il_proprietario_con_il_commento(doc, marta, luca, mailoutbox, django_capture_on_commit_callbacks):
    servizi.invia_in_revisione(marta, doc, [luca], SEQ)
    with django_capture_on_commit_callbacks(execute=True):
        servizi.decidi(luca, doc, False, "Rivedi le cifre")
    assert mailoutbox[-1].to == ["marta@esempio.test"] and "Rivedi le cifre" in mailoutbox[-1].body


# --- gare ----------------------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_due_revisori_liberi_che_approvano_insieme_ne_vince_uno(marta, luca, giulia):
    d = servizi.crea_documento(marta, "Gara", file_di_testo("testo"))
    servizi.invia_in_revisione(marta, d, [luca, giulia], LIB)
    esiti, barriera = [], threading.Barrier(2)

    def approva(u):
        try:
            barriera.wait()
            servizi.decidi(u, d, True)
            esiti.append("ok")
        except ErroreDiDominio as e:
            esiti.append(str(e))
        finally:
            connections.close_all()

    fili = [threading.Thread(target=approva, args=(u,)) for u in (luca, giulia)]
    [f.start() for f in fili]
    [f.join() for f in fili]
    assert sorted(esiti)[1] == "ok" and "già stata conclusa" in sorted(esiti)[0]
    assert Partecipante.objects.filter(decisione="approvato").count() == 1
    d.refresh_from_db()
    assert d.stato == Documento.Stato.APPROVATO


# --- dal web -------------------------------------------------------------------------------------

def test_dal_web_il_revisore_vede_i_pulsanti_solo_quando_tocca_a_lui(doc, marta, luca, giulia):
    servizi.invia_in_revisione(marta, doc, [luca, giulia], SEQ, "Controlla il capitolo 2")
    pagina_luca = client_di(luca).get(reverse("dettaglio", args=[doc.pk])).text
    pagina_giulia = client_di(giulia).get(reverse("dettaglio", args=[doc.pk])).text
    assert "Approva" in pagina_luca and "Controlla il capitolo 2" in pagina_luca
    assert "Approva" not in pagina_giulia
    assert "Annulla la revisione" not in pagina_luca  # solo il proprietario


def test_dal_web_si_sceglie_dagli_elenchi_e_htmx_riceve_il_frammento(doc, marta, luca, giulia):
    client = client_di(marta)
    risposta = client.post(reverse("invia_revisione", args=[doc.pk]),
                           {"revisore_1": luca.pk, "revisore_2": giulia.pk, "modalita": SEQ, "messaggio": "Ciao"},
                           headers={"HX-Request": "true"})
    assert risposta.status_code == 200 and "<html" not in risposta.text and 'id="flusso"' in risposta.text
    assert [p.utente.username for p in doc.revisioni.get().partecipanti.all()] == ["luca", "giulia"]


def test_dal_web_il_proprietario_non_e_fra_i_revisori_proponibili(doc, marta):
    pagina = client_di(marta).get(reverse("dettaglio", args=[doc.pk])).text
    assert "Revisore 1" in pagina and 'value="%d"' % marta.pk not in pagina.split("Revisore 1")[1].split("Modalità")[0]


def test_dal_web_decidere_con_errore_mostra_il_messaggio_non_un_500(doc, marta, luca, giulia):
    servizi.invia_in_revisione(marta, doc, [luca, giulia], SEQ)
    risposta = client_di(giulia).post(reverse("decidi", args=[doc.pk]), {"esito": "approva"}, follow=True)
    assert risposta.status_code == 200 and "turno" in risposta.text


def test_con_htmx_l_errore_sta_nel_frammento_non_nel_messaggio_successivo(doc, marta, luca, giulia):
    servizi.invia_in_revisione(marta, doc, [luca, giulia], SEQ)
    risposta = client_di(giulia).post(reverse("decidi", args=[doc.pk]), {"esito": "approva"},
                                      headers={"HX-Request": "true"})
    assert "Non è ancora il tuo turno" in risposta.text and "<html" not in risposta.text
    # ...e non riappare, già consumato, alla prossima pagina intera
    assert "Non è ancora il tuo turno" not in client_di(giulia).get(reverse("dettaglio", args=[doc.pk])).text
