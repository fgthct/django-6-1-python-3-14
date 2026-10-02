import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from articoli.models import Articolo


def png_valido():
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(buffer, format="PNG")
    return SimpleUploadedFile("copertina.png", buffer.getvalue(), content_type="image/png")


def dati_articolo(slug, **extra):
    dati = {
        "titolo": "Con copertina",
        "slug": slug,
        "sommario": "",
        "testo": "Testo dell'articolo",
        "tags": "",
        "metadati": "",
        "pubblicato": "on",
        "commenti-TOTAL_FORMS": "0",
        "commenti-INITIAL_FORMS": "0",
        "commenti-MIN_NUM_FORMS": "0",
        "commenti-MAX_NUM_FORMS": "1000",
    }
    dati.update(extra)
    return dati


@pytest.fixture(autouse=True)
def cartella_media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


def test_l_immagine_viene_accettata(admin_client):
    url = reverse("admin:articoli_articolo_add")
    risposta = admin_client.post(url, dati_articolo("con-png", copertina=png_valido()))
    assert risposta.status_code == 302
    assert Articolo.objects.get(slug="con-png").copertina.name.startswith("copertine/")


def test_un_file_di_testo_viene_rifiutato_dal_parser(admin_client):
    url = reverse("admin:articoli_articolo_add")
    testo = SimpleUploadedFile("note.txt", b"ciao", content_type="text/plain")
    risposta = admin_client.post(url, dati_articolo("con-txt", copertina=testo))
    assert risposta.status_code == 400
    assert not Articolo.objects.filter(slug="con-txt").exists()


def test_un_finto_png_supera_il_parser_ma_non_il_form(admin_client):
    # il tipo dichiarato è image/png, ma il contenuto non è un'immagine
    finto = SimpleUploadedFile("finto.png", b"non sono un'immagine", content_type="image/png")
    url = reverse("admin:articoli_articolo_add")
    risposta = admin_client.post(url, dati_articolo("finto", copertina=finto))
    assert risposta.status_code == 200          # il form mostra l'errore
    assert not Articolo.objects.filter(slug="finto").exists()
