import numpy as np
import pytest

from documenti import servizi
from documenti.models import Accesso, Chunk, Documento
from documenti.rag import NON_LO_SO, rispondi
from documenti.ricerca import cerca

from .conftest import file_di_testo, utente

pytestmark = pytest.mark.django_db

FERIE = "Ogni dipendente ha diritto a ventisei giorni di ferie all'anno."
SEGRETO = "Il piano di licenziamenti riservato prevede ferie forzate per trenta dipendenti."


@pytest.fixture
def indicizzati(marta, luca, django_capture_on_commit_callbacks):
    """Un documento di Marta e uno riservato di Luca, entrambi indicizzati."""
    with django_capture_on_commit_callbacks(execute=True):
        pubblico = servizi.crea_documento(marta, "Politica ferie", file_di_testo(FERIE))
        riservato = servizi.crea_documento(luca, "Piano riservato", file_di_testo(SEGRETO))
    return pubblico, riservato


def test_si_trovano_solo_i_documenti_che_si_possono_vedere(indicizzati, marta, giulia):
    # La domanda è quasi uguale al testo riservato: se la ricerca non filtrasse, vincerebbe quello.
    risultati = cerca(marta, "piano di licenziamenti riservato ferie forzate")
    assert {c.versione.documento.titolo for c in risultati} == {"Politica ferie"}
    assert cerca(giulia, "ferie") == []


def test_dopo_la_concessione_il_documento_compare_e_dopo_la_revoca_sparisce(indicizzati, marta, luca, giulia):
    _, riservato = indicizzati
    servizi.concedi_accesso(luca, riservato, giulia, Accesso.Livello.LETTURA)
    assert {c.versione.documento.titolo for c in cerca(giulia, "licenziamenti")} == {"Piano riservato"}
    servizi.revoca_accesso(luca, riservato, giulia)
    assert cerca(giulia, "licenziamenti") == []


def test_si_cerca_solo_nella_versione_corrente(marta, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        d = servizi.crea_documento(marta, "Doc", file_di_testo("Il magazzino si trova a nord."))
        servizi.carica_versione(marta, d, file_di_testo("Il deposito si trova a sud."))
    testi = [c.testo for c in cerca(marta, "dove si trova")]
    assert testi == ["Il deposito si trova a sud."]


def test_i_risultati_sono_ordinati_per_distanza(indicizzati, marta):
    risultati = cerca(marta, "giorni di ferie", limite=5)
    distanze = [c.distanza for c in risultati]
    assert distanze == sorted(distanze)


def test_la_risposta_cita_le_fonti_e_non_inventa(indicizzati, marta, giulia):
    r = rispondi(marta, "quanti giorni di ferie ho?")
    assert r.trovata and "ventisei" in r.testo and r.fonti[0].versione.documento.titolo == "Politica ferie"
    r = rispondi(giulia, "quanti giorni di ferie ho?")
    assert not r.trovata and r.testo == NON_LO_SO and r.fonti == []


def test_una_domanda_senza_relazione_con_i_documenti_non_ha_risposta(indicizzati, marta):
    assert not rispondi(marta, "calcio mercato attaccante").trovata


def test_la_ricerca_restituisce_i_risultati_anche_con_un_filtro_molto_selettivo(marta, giulia, settings):
    """L'utente vede pochissimo, il resto è di altri: la ricerca deve comunque restituire i suoi cinque passaggi.
    Attenzione: su una tabella così piccola il planner NON usa l'indice HNSW e questo test passa anche senza
    `hnsw.iterative_scan`. Il guasto vero lo riproduce esperimenti/filtro_hnsw.py (30.000 righe, indice usato)."""
    altri = [utente(f"altro{n}") for n in range(20)]
    rng = np.random.default_rng(7)
    righe = []
    for proprietario in altri:
        d = Documento.objects.create(titolo=f"di {proprietario}", proprietario=proprietario)
        from documenti.models import Versione

        v = Versione.objects.create(
            documento=d, numero=1, nome_file="a.txt", testo="x", hash="0" * 64, autore=proprietario
        )
        d.versione_corrente = v
        d.save()
        righe += [
            Chunk(
                versione=v, posizione=i, testo=f"altro {i}", embedding=rng.normal(size=768).astype(np.float32).tolist()
            )
            for i in range(150)
        ]
    mio = Documento.objects.create(titolo="Mio", proprietario=giulia)
    from documenti.models import Versione

    vm = Versione.objects.create(documento=mio, numero=1, nome_file="m.txt", testo="x", hash="1" * 64, autore=giulia)
    mio.versione_corrente = vm
    mio.save()
    righe += [
        Chunk(versione=vm, posizione=i, testo=f"mio {i}", embedding=rng.normal(size=768).astype(np.float32).tolist())
        for i in range(10)
    ]
    Chunk.objects.bulk_create(righe)
    risultati = cerca(giulia, "qualunque cosa", limite=5, vettore=rng.normal(size=768).astype(np.float32).tolist())
    assert len(risultati) == 5 and all(c.testo.startswith("mio") for c in risultati)
