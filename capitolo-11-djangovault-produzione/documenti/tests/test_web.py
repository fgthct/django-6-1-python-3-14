import re
from pathlib import Path

import pytest
from django.urls import reverse

from documenti import servizi
from documenti.models import Documento

from .conftest import client_di, file_di_testo

pytestmark = pytest.mark.django_db
RADICE = Path(__file__).resolve().parents[2]


def test_la_politica_di_sicurezza_e_su_ogni_pagina(doc, marta):
    risposta = client_di(marta).get(reverse("elenco"))
    politica = risposta["Content-Security-Policy"]
    assert "'unsafe-inline'" not in politica and "'unsafe-eval'" not in politica
    nonce = re.search(r"'nonce-([^']+)'", politica).group(1)
    assert f'<script nonce="{nonce}">' in risposta.text


def test_il_tema_e_solo_scuro_nel_foglio_di_stile():
    css = (RADICE / "static" / "vault.css").read_text().lower()
    assert "color-scheme: dark" in css
    assert not re.search(r"(background|background-color)\s*:\s*(#fff\b|#ffffff|white)", css)
    assert "prefers-color-scheme: light" not in css


def test_il_tema_scuro_e_dichiarato_al_browser_in_ogni_pagina(doc, marta):
    for url in (reverse("elenco"), reverse("dettaglio", args=[doc.pk]), reverse("login")):
        pagina = client_di(marta).get(url).text
        assert '<meta name="color-scheme" content="dark">' in pagina, url


def test_creare_un_documento_dal_web(marta):
    risposta = client_di(marta).post(
        reverse("nuovo"), {"titolo": "Verbale", "file": file_di_testo("Riunione di lunedì.")}
    )
    assert risposta.status_code == 302
    assert Documento.objects.get().titolo == "Verbale"


def test_un_file_non_di_testo_da_un_messaggio_e_nessun_documento(marta):
    from django.core.files.uploadedfile import SimpleUploadedFile

    risposta = client_di(marta).post(
        reverse("nuovo"), {"titolo": "X", "file": SimpleUploadedFile("x.bin", b"\xff\xfe")}, follow=True
    )
    assert "solo file di testo" in risposta.text and not Documento.objects.exists()


def test_la_ricerca_htmx_restituisce_il_frammento(doc, marta, django_capture_on_commit_callbacks):
    from documenti.indicizzazione import indicizza_versione

    indicizza_versione.call(versione_id=str(doc.versione_corrente.pk))
    risposta = client_di(marta).get(reverse("cerca"), {"q": "paragrafo"}, headers={"HX-Request": "true"})
    assert 'id="risultati"' in risposta.text and "<html" not in risposta.text and "Politica ferie" in risposta.text


def test_il_contenuto_e_il_titolo_sono_sempre_escapati(marta):
    d = servizi.crea_documento(marta, "<script>alert(1)</script>", file_di_testo("<img src=x onerror=alert(2)>"))
    pagina = client_di(marta).get(reverse("dettaglio", args=[d.pk])).text
    assert "<script>alert(1)</script>" not in pagina and "<img src=x" not in pagina
    assert "&lt;script&gt;" in pagina


def test_il_download_di_una_versione_importata_senza_file_funziona(doc, marta):
    v = doc.versione_corrente
    v.file.delete(save=False)
    v.file = ""
    v.save()
    risposta = client_di(marta).get(reverse("scarica", args=[doc.pk, 1]))
    assert risposta.status_code == 200 and b"Primo paragrafo" in risposta.content
