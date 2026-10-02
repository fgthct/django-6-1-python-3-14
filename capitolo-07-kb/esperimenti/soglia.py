"""Quanto è lontano il miglior chunk, per domande in tema e fuori tema?"""
from esperimenti import prelude  # noqa: F401
from conoscenza import ricerca
from conoscenza.valutazione import DOMANDE

FUORI_TEMA = [
    "Qual è la capitale dell'Australia?",
    "Come si prepara la carbonara?",
    "Chi ha vinto il campionato di calcio nel 2010?",
    "Quanto costa un biglietto per la luna?",
    "Spiegami la teoria della relatività",
    "Che tempo farà domani a Catania?",
]


def migliore(q):
    return ricerca.cerca_per_significato(q, 1)[0].distanza


dentro = sorted(migliore(d.testo) for d in DOMANDE if d.tipo == "parafrasi")
fuori = sorted(migliore(q) for q in FUORI_TEMA)
print("in tema   :", " ".join(f"{x:.2f}" for x in dentro))
print("fuori tema:", " ".join(f"{x:.2f}" for x in fuori))
