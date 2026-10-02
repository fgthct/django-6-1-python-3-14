import pytest
from django.contrib.postgres.search import SearchQuery
from django.db import IntegrityError, connection

from conoscenza.models import Chunk, Documento

pytestmark = pytest.mark.django_db


def nuovo_doc(n=0):
    return Documento.objects.create(percorso=f"d{n}.md", titolo=f"Doc {n}", hash="h")


def test_l_id_e_un_uuid7_generato_dal_database():
    d = nuovo_doc()
    assert d.id.version == 7
    with connection.cursor() as c:
        c.execute("SELECT column_default FROM information_schema.columns "
                  "WHERE table_name='conoscenza_documento' AND column_name='id'")
        assert "uuidv7" in c.fetchone()[0].lower()


def test_gli_uuid7_seguono_l_ordine_di_creazione():
    creati = [nuovo_doc(i).id for i in range(30)]
    assert creati == sorted(creati)


def test_il_cascade_lo_fa_il_database():
    d = nuovo_doc()
    Chunk.objects.create(documento=d, posizione=0, testo="x")
    with connection.cursor() as c:
        # niente ORM: se il vincolo è nel database, la riga figlia sparisce lo stesso
        c.execute("DELETE FROM conoscenza_documento")
    assert Chunk.objects.count() == 0


def trova(parola):
    return Chunk.objects.filter(ricerca=SearchQuery(parola, config="italian"))


def test_la_colonna_ricerca_e_calcolata_e_si_aggiorna():
    d = nuovo_doc()
    c = Chunk.objects.create(documento=d, posizione=0, sezione="Ferie", testo="Le vacanze estive")
    assert trova("vacanza").exists()  # lo stemmer italiano
    assert not trova("malattia").exists()
    c.testo = "Il certificato di malattia"
    c.save()
    assert trova("malattia").exists()
    assert not trova("vacanza").exists()


def test_una_posizione_per_documento():
    d = nuovo_doc()
    Chunk.objects.create(documento=d, posizione=0, testo="a")
    with pytest.raises(IntegrityError):
        Chunk.objects.create(documento=d, posizione=0, testo="b")


def test_gli_indici_esistono():
    with connection.cursor() as c:
        c.execute("SELECT indexname, indexdef FROM pg_indexes WHERE tablename='conoscenza_chunk'")
        indici = dict(c.fetchall())
    assert "USING hnsw" in indici["chunk_embedding_hnsw"]
    assert "vector_cosine_ops" in indici["chunk_embedding_hnsw"]
    assert "USING gin" in indici["chunk_ricerca_gin"]
