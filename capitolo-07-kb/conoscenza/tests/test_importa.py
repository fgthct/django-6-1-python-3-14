import shutil

import pytest
from django.conf import settings
from django.core.management import call_command

from conoscenza import embedder
from conoscenza.models import Chunk, Documento

pytestmark = pytest.mark.django_db


@pytest.fixture
def cartella(tmp_path):
    shutil.copytree("documenti", tmp_path / "doc")
    return tmp_path / "doc"


def importa(cartella, *args):
    call_command("importa", str(cartella), *args, verbosity=0)


def test_importa_tutto(cartella):
    importa(cartella)
    assert Documento.objects.count() == 6
    assert Chunk.objects.exclude(embedding=None).count() == Chunk.objects.count() > 6
    assert set(Chunk.objects.values_list("modello", flat=True)) == {settings.EMBEDDING_MODELLO}


def test_e_idempotente(cartella):
    importa(cartella)
    prima = set(Chunk.objects.values_list("id", flat=True))
    importa(cartella)
    assert set(Chunk.objects.values_list("id", flat=True)) == prima  # nemmeno un chunk rifatto


def test_un_documento_modificato_si_rifa_e_gli_altri_no(cartella):
    importa(cartella)
    altri = set(Chunk.objects.exclude(documento__percorso="ferie_e_permessi.md").values_list("id", flat=True))
    vecchi = set(Chunk.objects.filter(documento__percorso="ferie_e_permessi.md").values_list("id", flat=True))
    f = cartella / "ferie_e_permessi.md"
    f.write_text(f.read_text().replace("26 giorni", "28 giorni"))
    importa(cartella)
    assert altri <= set(Chunk.objects.values_list("id", flat=True))
    nuovi = set(Chunk.objects.filter(documento__percorso="ferie_e_permessi.md").values_list("id", flat=True))
    assert nuovi and nuovi.isdisjoint(vecchi)
    assert Chunk.objects.filter(testo__contains="28 giorni").exists()


def test_se_cambia_il_modello_si_rifanno_i_vettori_anche_a_testo_invariato(cartella, settings):
    importa(cartella)
    settings.EMBEDDING_MODELLO = "un/altro-modello"
    importa(cartella)
    assert set(Chunk.objects.values_list("modello", flat=True)) == {"un/altro-modello"}


def test_forza_rifa_tutto(cartella):
    importa(cartella)
    prima = set(Chunk.objects.values_list("id", flat=True))
    importa(cartella, "--forza")
    assert set(Chunk.objects.values_list("id", flat=True)).isdisjoint(prima)


def test_gli_orfani_si_eliminano_solo_su_richiesta(cartella):
    importa(cartella)
    (cartella / "nuovi_assunti.md").unlink()
    importa(cartella)
    assert Documento.objects.count() == 6
    importa(cartella, "--elimina-orfani")
    assert Documento.objects.count() == 5
    assert not Chunk.objects.filter(documento__percorso="nuovi_assunti.md").exists()


def test_un_modello_con_le_dimensioni_sbagliate_e_un_errore_chiaro(cartella, monkeypatch):
    class Corto:
        def embed(self, testi):
            for _ in testi:
                yield __import__("numpy").zeros(384)

    monkeypatch.setattr(embedder, "_modello", lambda: Corto())
    with pytest.raises(ValueError, match="384 dimensioni"):
        importa(cartella)
    assert Documento.objects.count() == 0  # niente a metà


def test_se_l_inserimento_fallisce_il_documento_resta_com_era(cartella, monkeypatch):
    importa(cartella)
    prima = set(Chunk.objects.values_list("id", flat=True))
    f = cartella / "ferie_e_permessi.md"
    f.write_text(f.read_text().replace("26 giorni", "28 giorni"))

    def guasto(*a, **k):
        raise RuntimeError("disco pieno")

    monkeypatch.setattr(Chunk.objects, "bulk_create", guasto)
    with pytest.raises(RuntimeError):
        importa(cartella)
    # il vecchio contenuto è intatto: la cancellazione dei chunk è stata annullata
    assert set(Chunk.objects.values_list("id", flat=True)) == prima
    assert not Chunk.objects.filter(testo__contains="28 giorni").exists()
