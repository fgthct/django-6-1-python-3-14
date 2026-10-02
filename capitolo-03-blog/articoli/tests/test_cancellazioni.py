from articoli import signals
from articoli.models import Categoria, Commento

from .conftest import crea_articolo


def test_eliminare_un_commento_invia_il_segnale(articoli):
    commento = Commento.objects.create(articolo=articoli["etna"], autore="A", testo="x")
    signals.commenti_eliminati.clear()
    commento.delete()
    assert len(signals.commenti_eliminati) == 1


def test_db_cascade_elimina_i_commenti_ma_non_invia_segnali(articoli):
    etna = articoli["etna"]
    for autore in ("A", "B", "C"):
        Commento.objects.create(articolo=etna, autore=autore, testo="x")
    signals.commenti_eliminati.clear()

    etna.delete()

    assert Commento.objects.filter(autore__in=["A", "B", "C"]).count() == 0
    assert signals.commenti_eliminati == []


def test_db_set_null_azzera_la_categoria(articoli):
    articolo = articoli["arancino"]
    assert articolo.categoria is not None
    Categoria.objects.get(slug="cucina").delete()
    articolo.refresh_from_db()
    assert articolo.categoria is None
