"""Due errori tipici con gli embedding: uno rumoroso, uno silenzioso."""
import numpy as np
from django.db import DataError

from esperimenti import prelude  # noqa: F401
from frasi.models import Frase
from frasi.ricerca import cerca_per_significato

# 1) Dimensione sbagliata: il database protesta subito.
try:
    list(cerca_per_significato("x", vettore=[0.1] * 384))
except DataError as errore:
    print("1) vettore da 384 dimensioni contro una colonna da 768:")
    print("   ", str(errore).splitlines()[0])

# 2) Stessa dimensione, ma vettore che NON viene dal modello giusto: nessun errore.
rng = np.random.default_rng(7)
estraneo = rng.normal(size=768)
estraneo /= np.linalg.norm(estraneo)
print("\n2) vettore casuale da 768 dimensioni (nessun errore, nessun avviso):")
for f in cerca_per_significato("x", limite=3, vettore=estraneo.tolist()):
    print(f"    {f.distanza:.3f}  [{f.argomento}] {f.testo[:55]}")
print(f"    ({Frase.objects.count()} frasi nel corpus: i risultati sembrano risposte, ma non lo sono)")
