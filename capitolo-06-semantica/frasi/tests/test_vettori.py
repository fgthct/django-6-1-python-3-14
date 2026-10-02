import os

import numpy as np
import pytest
from django.conf import settings
from django.core.management import call_command
from django.db import DataError, connection, transaction
from pgvector.django import L2Distance

from frasi import embedder
from frasi.models import Frase, PuntoProva
from frasi.ricerca import cerca_per_parole, cerca_per_significato

from .conftest import vettore


def test_la_colonna_ha_la_dimensione_del_modello():
    assert Frase._meta.get_field("embedding").dimensions == settings.EMBEDDING_DIMENSIONI


def test_un_vettore_di_dimensione_sbagliata_viene_rifiutato(db):
    with pytest.raises(DataError), transaction.atomic():
        Frase.objects.create(testo="x", argomento="t", embedding=[0.1] * 3)


def test_l_ordine_e_per_distanza_coseno(frasi_a_mano):
    ordine = [f.testo[0] for f in cerca_per_significato("x", vettore=vettore(1, 0))]
    # a punta nella stessa direzione della domanda (anche se è corto): è il più vicino.
    # Con la distanza L2 l'ordine sarebbe c, a, b; con il prodotto scalare b, c, a.
    assert ordine == ["a", "c", "b"]


def test_la_distanza_coseno_ignora_la_lunghezza(frasi_a_mano):
    d = {f.testo[0]: f.distanza for f in cerca_per_significato("x", vettore=vettore(1, 0))}
    assert d["a"] == pytest.approx(0, abs=1e-6)


def test_vettori_ortogonali_hanno_distanza_uno(db):
    Frase.objects.create(testo="o", argomento="t", embedding=vettore(0, 1))
    (frase,) = cerca_per_significato("x", vettore=vettore(1, 0))
    assert frase.distanza == pytest.approx(1.0)


def test_le_frasi_senza_embedding_non_compaiono(frasi_a_mano):
    Frase.objects.create(testo="senza", argomento="t")
    risultati = list(cerca_per_significato("x", vettore=vettore(1, 0), limite=10))
    assert len(risultati) == 3 and all(f.embedding is not None for f in risultati)


def test_la_ricerca_per_parole_richiede_i_termini(db):
    Frase.objects.create(testo="Come si prepara l'arancino siciliano", argomento="cucina")
    assert [f.argomento for f in cerca_per_parole("arancino")] == ["cucina"]
    assert list(cerca_per_parole("piatto fritto di riso")) == []  # niente parole in comune: niente risultati


def test_i_risultati_con_distanze_uguali_hanno_un_ordine_stabile(db):
    ids = [Frase.objects.create(testo=f"f{i}", argomento="t", embedding=vettore(1, 0)).pk for i in range(4)]
    assert [f.pk for f in cerca_per_significato("x", vettore=vettore(1, 0), limite=4)] == ids


def test_l_indice_hnsw_serve_la_distanza_coseno_e_non_la_l2(db):
    PuntoProva.objects.create(gruppo=1, embedding=vettore(1, 0))

    def piano(espressione):
        with connection.cursor() as c:
            c.execute("SET enable_seqscan = off")
            sql, parametri = PuntoProva.objects.order_by(espressione)[:3].query.sql_with_params()
            c.execute("EXPLAIN " + sql, parametri)
            return "\n".join(r[0] for r in c.fetchall())

    from pgvector.django import CosineDistance
    assert "puntoprova_hnsw" in piano(CosineDistance("embedding", vettore(1, 0)))
    assert "puntoprova_hnsw" not in piano(L2Distance("embedding", vettore(1, 0)))


def test_incorpora_rifiuta_un_modello_con_la_dimensione_sbagliata(monkeypatch):
    class Finto:
        def embed(self, testi):
            return [np.zeros(10) for _ in testi]

    monkeypatch.setattr(embedder, "_modello", lambda: Finto())
    with pytest.raises(ValueError, match="10 dimensioni"):
        embedder.incorpora(["x"])


def test_carica_frasi_e_ripetibile(db, monkeypatch):
    chiamate = []

    def finto(testi):
        chiamate.append(len(testi))
        return [vettore(1.0)] * len(testi)

    monkeypatch.setattr("frasi.management.commands.carica_frasi.incorpora", finto)
    call_command("carica_frasi")
    call_command("carica_frasi")
    assert Frase.objects.count() == 40
    assert chiamate == [40]  # la seconda volta non c'è niente da calcolare
    assert not Frase.objects.filter(embedding=None).exists()


@pytest.mark.skipif(not os.environ.get("TEST_MODELLO"), reason="scarica e carica il modello vero (lento)")
def test_il_modello_vero_avvicina_le_frasi_simili(db):
    testi = ["Come si prepara l'arancino siciliano", "Il supplì romano: riso fritto con mozzarella",
             "La borsa di Milano chiude in rialzo"]
    for t, v in zip(testi, embedder.incorpora(testi), strict=True):
        Frase.objects.create(testo=t, argomento="t", embedding=v)
    vicine = [f.testo for f in cerca_per_significato(testi[0], limite=3)]
    assert vicine.index(testi[1]) < vicine.index(testi[2])


def test_la_ricerca_ha_un_ordinamento_totale(db):
    # Distanze uguali sono normali (vettori duplicati, testi quasi identici):
    # senza un criterio di riserva l'ordine tra pari merito non è garantito.
    assert cerca_per_significato("x", vettore=vettore(1, 0)).totally_ordered


def test_i_modelli_e_le_migrazioni_sono_allineati(db):
    # Un indice è definito dalla migrazione, non dal modello: se qualcuno cambia
    # il modello (per esempio l'operatore dell'indice) senza creare la migrazione,
    # il database resta com'era e nessun altro test se ne accorge.
    call_command("makemigrations", "--check", "--dry-run")
