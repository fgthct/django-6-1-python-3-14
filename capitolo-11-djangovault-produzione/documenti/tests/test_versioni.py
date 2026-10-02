import threading

import pytest
from django.core.exceptions import PermissionDenied
from django.db import connections

from documenti import servizi
from documenti.chunking import spezza
from documenti.indicizzazione import indicizza_versione
from documenti.models import Accesso, Chunk, Documento, Versione
from documenti.servizi import ErroreDiDominio

from .conftest import file_di_testo

pytestmark = pytest.mark.django_db


def test_creare_un_documento_crea_la_versione_uno(doc, marta, settings):
    v = doc.versione_corrente
    assert (v.numero, v.autore, v.nota) == (1, marta, "Prima stesura")
    assert len(v.hash) == 64 and v.testo.startswith("Primo paragrafo")
    assert (settings.MEDIA_ROOT / v.file.name).read_text() == v.testo
    assert doc.stato == Documento.Stato.BOZZA


def test_ogni_caricamento_aggiunge_una_versione_senza_toccare_le_vecchie(doc, marta):
    servizi.carica_versione(marta, doc, file_di_testo("Testo nuovo."), "Seconda")
    doc.refresh_from_db()
    assert [v.numero for v in doc.versioni.all()] == [2, 1]
    assert doc.versione_corrente.numero == 2
    assert Versione.objects.get(documento=doc, numero=1).testo.startswith("Primo paragrafo")


def test_un_file_identico_alla_versione_corrente_e_rifiutato(doc, marta):
    with pytest.raises(ErroreDiDominio, match="identico"):
        servizi.carica_versione(marta, doc, file_di_testo())
    assert doc.versioni.count() == 1


def test_solo_file_di_testo(marta):
    from django.core.files.uploadedfile import SimpleUploadedFile

    with pytest.raises(ErroreDiDominio, match="testo"):
        servizi.crea_documento(marta, "Binario", SimpleUploadedFile("x.bin", b"\xff\xfe\x00\x01"))
    with pytest.raises(ErroreDiDominio, match="testo"):
        servizi.crea_documento(marta, "Nul", SimpleUploadedFile("x.bin", b"abc\x00def"))
    assert not Documento.objects.exists()


def test_file_troppo_grande(marta, settings):
    settings.DIMENSIONE_MASSIMA_FILE = 10
    with pytest.raises(ErroreDiDominio, match="grande"):
        servizi.crea_documento(marta, "Grande", file_di_testo("x" * 11))


def test_un_lettore_non_carica_versioni_un_editor_si(doc, marta, luca, giulia):
    servizi.concedi_accesso(marta, doc, luca, Accesso.Livello.LETTURA)
    servizi.concedi_accesso(marta, doc, giulia, Accesso.Livello.MODIFICA)
    with pytest.raises(PermissionDenied):
        servizi.carica_versione(luca, doc, file_di_testo("Di Luca"))
    assert servizi.carica_versione(giulia, doc, file_di_testo("Di Giulia")).numero == 2


def test_una_versione_nuova_di_un_documento_approvato_lo_riporta_in_bozza(doc, marta, luca):
    servizi.invia_in_revisione(marta, doc, [luca], "sequenza")
    servizi.decidi(luca, doc, True)
    doc.refresh_from_db()
    assert doc.stato == Documento.Stato.APPROVATO
    servizi.carica_versione(marta, doc, file_di_testo("Cambiato."))
    doc.refresh_from_db()
    assert doc.stato == Documento.Stato.BOZZA


def test_i_file_orfani_non_restano_sul_disco_se_la_transazione_fallisce(marta, settings, monkeypatch):
    def guasto(*a, **k):
        raise RuntimeError("guasto dopo la scrittura del file")

    monkeypatch.setattr(servizi, "_evento", guasto)
    with pytest.raises(RuntimeError):
        servizi.crea_documento(marta, "Fallito", file_di_testo())
    assert not Documento.objects.exists()
    assert [p for p in settings.MEDIA_ROOT.rglob("*") if p.is_file()] == []


def test_l_indicizzazione_dopo_il_commit_e_si_puo_ripetere(marta, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        d = servizi.crea_documento(marta, "Doc", file_di_testo("Uno.\n\nDue.\n\nTre."))
    v = d.versione_corrente
    prima = list(v.chunk.values_list("testo", flat=True))
    assert prima and all(c.embedding is not None for c in v.chunk.all())
    indicizza_versione.call(versione_id=str(v.pk))
    assert list(v.chunk.values_list("testo", flat=True)) == prima  # nessun duplicato
    assert Chunk.objects.count() == len(prima)


@pytest.mark.django_db(transaction=True)
def test_due_caricamenti_insieme_non_prendono_lo_stesso_numero(marta):
    d = servizi.crea_documento(marta, "Gara", file_di_testo("v1"))
    errori, numeri = [], []

    def carica(n):
        try:
            numeri.append(servizi.carica_versione(marta, d, file_di_testo(f"versione {n}")).numero)
        except Exception as e:  # noqa: BLE001
            errori.append(e)
        finally:
            connections.close_all()

    fili = [threading.Thread(target=carica, args=(n,)) for n in range(4)]
    [f.start() for f in fili]
    [f.join() for f in fili]
    assert errori == [] and sorted(numeri) == [2, 3, 4, 5]


@pytest.mark.parametrize("testo, massimo", [("a b c " * 200, 50), ("x" * 500, 100), ("\n\n\n", 50), ("", 50)])
def test_i_passaggi_non_superano_il_massimo_e_non_perdono_testo(testo, massimo):
    passaggi = spezza(testo, massimo)
    assert all(len(p) <= massimo for p in passaggi)
    assert "".join(passaggi).replace(" ", "").replace("\n", "") == testo.replace(" ", "").replace("\n", "")
