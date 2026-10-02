from articoli.archivio import leggi_archivio, scrivi_archivio


def test_archivio_andata_e_ritorno(articoli, tmp_path):
    percorso = tmp_path / "archivio.json.zst"
    totale = scrivi_archivio(percorso)
    dati = leggi_archivio(percorso)
    assert totale == 3                      # la bozza non viene archiviata
    assert {d["slug"] for d in dati} == {"arancino", "etna", "viaggio"}
    assert percorso.read_bytes()[:4] == b"\x28\xb5\x2f\xfd"   # firma di Zstandard
