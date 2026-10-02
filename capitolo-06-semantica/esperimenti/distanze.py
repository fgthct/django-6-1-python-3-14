"""Le tre distanze di pgvector su due vettori piccoli, e su vettori normalizzati."""
import numpy as np
from django.db import connection

from esperimenti import prelude  # noqa: F401
from frasi.embedder import incorpora

with connection.cursor() as c:
    c.execute("SELECT '[3,4]'::vector <-> '[0,0]'::vector, '[1,0]'::vector <=> '[0,1]'::vector, "
              "'[1,2]'::vector <#> '[3,4]'::vector")
    l2, coseno, prodotto = c.fetchone()
print(f"<->  distanza L2 tra [3,4] e [0,0]            = {l2}")
print(f"<=>  distanza coseno tra [1,0] e [0,1]        = {coseno}")
print(f"<#>  prodotto scalare negato tra [1,2] e [3,4] = {prodotto}")

# Tre vettori fatti a mano, nel piano. La domanda è [1, 0].
# a punta nella stessa direzione ma è corto; b è lunghissimo e leggermente storto; c è quasi uguale.
print("\nVettori a mano. Domanda = [1,0]; a = [0.5,0]; b = [10,2]; c = [0.9,0.1]")
with connection.cursor() as cur:
    for nome, op in {"L2": "<->", "coseno": "<=>", "prodotto scalare negato": "<#>"}.items():
        cur.execute(f"""
            SELECT nome FROM (VALUES ('a','[0.5,0]'::vector), ('b','[10,2]'::vector), ('c','[0.9,0.1]'::vector))
            AS t(nome, v) ORDER BY v {op} '[1,0]'::vector""")
        print(f"{nome:<26} dal più vicino al più lontano: {[r[0] for r in cur.fetchall()]}")

testi = [
    "Come si prepara l'arancino siciliano con ragù e piselli",   # 0: la domanda
    "Il supplì romano: riso fritto con mozzarella filante",       # 1
    "La borsa di Milano chiude in rialzo trainata dalle banche",  # 2
    "L'Etna è tornato in eruzione: colate laviche sul versante sud",  # 3
    "Pasta alla Norma: melanzane fritte, pomodoro e ricotta salata",  # 4
]
V = np.array(incorpora(testi))
print("\nNorma dei vettori del modello:", np.round(np.linalg.norm(V, axis=1), 3).tolist())
q = V[0]
for nome, d in {
    "coseno": 1 - (V @ q) / (np.linalg.norm(V, axis=1) * np.linalg.norm(q)),
    "L2": np.linalg.norm(V - q, axis=1),
    "prodotto scalare (negato)": -(V @ q),
}.items():
    print(f"{nome:<28} ordine: {np.argsort(d).tolist()}")
Vn = V / np.linalg.norm(V, axis=1, keepdims=True)
qn = Vn[0]
print("\nDopo la normalizzazione (norma = 1):")
for nome, d in {"coseno": 1 - Vn @ qn, "L2": np.linalg.norm(Vn - qn, axis=1), "prodotto scalare (negato)": -(Vn @ qn)}.items():
    print(f"{nome:<28} ordine: {np.argsort(d).tolist()}")
