import pytest

from conoscenza import ricerca

pytestmark = pytest.mark.django_db


def test_per_significato_ordina_per_distanza(corpus):
    ris = list(ricerca.cerca_per_significato("rimborso chilometrico auto propria", 3))
    assert ris[0].documento.percorso == "rimborsi_spese.md"
    distanze = [c.distanza for c in ris]
    assert distanze == sorted(distanze)


def test_per_parole_trova_il_codice_esatto(corpus):
    ris = list(ricerca.cerca_per_parole("RS-12", 5))
    assert [c.documento.percorso for c in ris] == ["rimborsi_spese.md"]


def test_una_domanda_lunga_in_and_non_trova_niente_in_or_si(corpus):
    domanda = "Quanti giorni di vacanza spettano in un anno?"
    assert list(ricerca.cerca_per_parole(domanda, 5, tutte_le_parole=True)) == []
    assert list(ricerca.cerca_per_parole(domanda, 5)) != []


def test_il_filtro_sulla_ricerca_evita_i_risultati_senza_corrispondenza(corpus):
    assert list(ricerca.cerca_per_parole("zxqvw", 5)) == []


def test_ibrida_unisce_le_due_liste(corpus):
    ris = ricerca.cerca_ibrida("modulo RS-12 rimborso", 3)
    primo = ris[0]
    assert primo.chunk.documento.percorso == "rimborsi_spese.md"
    assert primo.posizione_significato is not None and primo.posizione_parole is not None
    assert [r.punteggio for r in ris] == sorted((r.punteggio for r in ris), reverse=True)


def test_ibrida_rispetta_il_limite(corpus):
    assert len(ricerca.cerca_ibrida("lavoro", 2)) == 2


def test_ibrida_funziona_anche_quando_le_parole_non_trovano_nulla(corpus):
    ris = ricerca.cerca_ibrida("Quanti giorni di vacanza spettano in un anno?", 3)
    assert ris and all(r.posizione_parole is None for r in ris)


def test_senza_chunk_nessun_risultato(db):
    assert ricerca.cerca_ibrida("qualsiasi cosa") == []


@pytest.mark.parametrize(
    "impostazioni",
    ["SET LOCAL enable_seqscan = off", "SET LOCAL enable_indexscan = off; SET LOCAL enable_bitmapscan = off"],
    ids=["con indice", "senza indice"],
)
def test_i_chunk_senza_embedding_non_compaiono_con_nessun_piano(corpus, impostazioni):
    """L'indice HNSW salta da solo i NULL, la scansione sequenziale no.

    Senza `exclude(embedding=None)` il risultato dipenderebbe dal piano scelto
    da PostgreSQL, cioè dalle statistiche della tabella: un bug che compare e
    scompare. Qui forziamo entrambi i piani.
    """
    from django.db import connection
    from conoscenza.models import Chunk

    Chunk.objects.update(embedding=None)
    with connection.cursor() as c:
        c.execute(impostazioni)
    assert list(ricerca.cerca_per_significato("ferie", 5)) == []


def test_ibrida_fonde_davvero_le_due_liste(monkeypatch):
    class F:  # un chunk finto: serve solo la chiave primaria
        def __init__(self, pk):
            self.pk = pk

    a, b, c = F("a"), F("b"), F("c")
    monkeypatch.setattr(ricerca, "cerca_per_significato", lambda *x, **k: [a, b, c])
    monkeypatch.setattr(ricerca, "cerca_per_parole", lambda *x, **k: [c])
    ris = ricerca.cerca_ibrida("qualsiasi", 3)
    assert [r.chunk.pk for r in ris] == ["c", "a", "b"]  # c è in entrambe: sale in testa
    assert (ris[0].posizione_significato, ris[0].posizione_parole) == (3, 1)
