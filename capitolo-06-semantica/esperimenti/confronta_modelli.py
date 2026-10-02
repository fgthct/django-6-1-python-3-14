"""Stesse domande, due modelli: quanto conta la scelta del modello?"""
import numpy as np
from django.conf import settings
from fastembed import TextEmbedding

from esperimenti import prelude  # noqa: F401  (configura Django)
from frasi.corpus import CORPUS

MODELLI = [
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
]
DOMANDE = ["piatto fritto di riso con ragù", "la montagna di fuoco si risveglia", "quanto costa un mutuo"]

testi = [(argomento, t) for argomento, lista in CORPUS.items() for t in lista]

for nome in MODELLI:
    modello = TextEmbedding(nome, cache_dir=settings.EMBEDDING_CACHE)
    V = np.array(list(modello.embed([t for _, t in testi])))
    V /= np.linalg.norm(V, axis=1, keepdims=True)
    print(f"\n{nome.split('/')[1]}  ({V.shape[1]} dimensioni)")
    for domanda in DOMANDE:
        q = np.array(list(modello.embed([domanda])))[0]
        q /= np.linalg.norm(q)
        distanze = 1 - V @ q
        primi = np.argsort(distanze)[:3]
        giusti = sum(testi[i][0] == testi[primi[0]][0] for i in primi)
        print(f"  «{domanda}»")
        for i in primi:
            print(f"    {distanze[i]:.3f}  [{testi[i][0]}] {testi[i][1][:58]}")
