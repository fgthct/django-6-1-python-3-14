import re
import zlib

import numpy as np
import pytest
from django.conf import settings
from django.core.management import call_command

from conoscenza import embedder


class ModelloFinto:
    """Un «modello» deterministico: ogni parola accende una dimensione.

    Non capisce i sinonimi, ma è istantaneo, riproducibile e rispetta il
    contratto di fastembed (`embed` produce array numpy). Ci basta per
    provare *il nostro* codice: chunking, import, SQL, fusione.
    """

    def embed(self, testi):
        for testo in testi:
            v = np.zeros(settings.EMBEDDING_DIMENSIONI, dtype=np.float32)
            for parola in re.findall(r"\w+", testo.lower()):
                v[zlib.crc32(parola.encode()) % settings.EMBEDDING_DIMENSIONI] += 1.0
            yield v


@pytest.fixture(autouse=True)
def modello_finto(request, monkeypatch):
    if request.node.get_closest_marker("modello_vero"):
        return
    embedder._modello.cache_clear()
    monkeypatch.setattr(embedder, "_modello", lambda: ModelloFinto())


@pytest.fixture
def corpus(db):
    """I sei documenti del progetto, importati."""
    call_command("importa", "documenti", verbosity=0)
