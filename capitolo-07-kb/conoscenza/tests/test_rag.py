import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from conoscenza import rag

pytestmark = pytest.mark.django_db


def test_risponde_con_il_passaggio_e_le_fonti(corpus):
    r = rag.rispondi("modulo RS-12 per il rimborso")
    assert r.trovata
    assert "RS-12" in r.testo
    assert r.fonti[0].chunk.documento.percorso == "rimborsi_spese.md"


def test_oltre_la_soglia_dice_che_non_lo_sa(corpus, settings):
    settings.RAG_DISTANZA_MASSIMA = 0.0
    r = rag.rispondi("modulo RS-12 per il rimborso")
    assert not r.trovata and r.fonti == [] and r.testo == rag.NON_LO_SO


def test_il_generatore_riceve_prompt_e_passaggi(corpus, settings, monkeypatch):
    viste = {}

    def finto(prompt, passaggi):
        viste.update(prompt=prompt, passaggi=passaggi)
        return "risposta generata"

    monkeypatch.setitem(rag.GENERATORI, "estrattivo", finto)
    r = rag.rispondi("modulo RS-12 per il rimborso")
    assert r.testo == "risposta generata"
    assert len(viste["passaggi"]) <= settings.RAG_CHUNK_NEL_CONTESTO
    assert "Domanda: modulo RS-12 per il rimborso" in viste["prompt"]


def test_il_generatore_ollama_parla_il_protocollo_giusto(settings):
    ricevuto = {}

    class Gestore(BaseHTTPRequestHandler):
        def do_POST(self):
            ricevuto["path"] = self.path
            ricevuto["corpo"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            risposta = json.dumps({"response": "  ecco la risposta \n"}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(risposta)))
            self.end_headers()
            self.wfile.write(risposta)

        def log_message(self, *a):
            pass

    server = HTTPServer(("127.0.0.1", 0), Gestore)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        settings.OLLAMA_URL = f"http://127.0.0.1:{server.server_port}"
        settings.OLLAMA_MODELLO = "modello-di-prova"
        assert rag.genera_ollama("il prompt", ["p"]) == "ecco la risposta"
    finally:
        server.shutdown()
    assert ricevuto["path"] == "/api/generate"
    assert ricevuto["corpo"] == {"model": "modello-di-prova", "prompt": "il prompt", "stream": False}
