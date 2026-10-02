"""Indice HNSW: velocità e precisione (recall) su 20.000 vettori sintetici."""
import time

import numpy as np
from django.db import connection

from esperimenti import prelude  # noqa: F401
from frasi.models import PuntoProva

N, DIM, GRUPPI, K, N_QUERY = 20_000, 768, 40, 10, 100
rng = np.random.default_rng(42)  # seme fisso: i risultati sono ripetibili

centri = rng.normal(size=(GRUPPI, DIM))


def genera(n):
    gruppi = rng.integers(0, GRUPPI, size=n)
    punti = centri[gruppi] + 0.7 * rng.normal(size=(n, DIM))
    return gruppi, punti / np.linalg.norm(punti, axis=1, keepdims=True)


gruppi, V = genera(N)
_, Q = genera(N_QUERY)

with connection.cursor() as c:
    c.execute("TRUNCATE frasi_puntoprova")  # svuota davvero (un delete lascerebbe righe morte)
    c.execute("DROP INDEX IF EXISTS puntoprova_hnsw")  # si carica prima, si indicizza dopo

t = time.perf_counter()
PuntoProva.objects.bulk_create(
    [PuntoProva(gruppo=int(g), embedding=v.tolist()) for g, v in zip(gruppi, V)], batch_size=1000
)
print(f"Inserite {N} righe da {DIM} dimensioni in {time.perf_counter() - t:.1f} s")

with connection.cursor() as c:
    c.execute("SELECT pg_size_pretty(pg_total_relation_size('frasi_puntoprova')), "
              "pg_column_size(embedding) FROM frasi_puntoprova LIMIT 1")
    print("Tabella (senza indice): %s; un vettore occupa %d byte" % c.fetchone())

    t = time.perf_counter()
    c.execute("CREATE INDEX puntoprova_hnsw ON frasi_puntoprova USING hnsw (embedding vector_cosine_ops) "
              "WITH (m = 16, ef_construction = 64)")
    print(f"Indice HNSW creato in {time.perf_counter() - t:.1f} s")
    c.execute("SELECT pg_size_pretty(pg_relation_size('puntoprova_hnsw'))")
    print("Dimensione dell'indice:", c.fetchone()[0])
    c.execute("ANALYZE frasi_puntoprova")

    q0 = "[" + ",".join(f"{x:.6f}" for x in Q[0]) + "]"
    c.execute(f"EXPLAIN SELECT id FROM frasi_puntoprova ORDER BY embedding <=> '{q0}' LIMIT {K}")
    print("\nPiano di esecuzione:")
    for riga in c.fetchall():
        print("  ", riga[0][:100] + ("…" if len(riga[0]) > 100 else ""))

# Risposta esatta, calcolata con numpy: è il "giusto" con cui confrontare l'indice.
ids = np.array(list(PuntoProva.objects.order_by("pk").values_list("pk", flat=True)))
esatti = [set(ids[np.argsort(1 - V @ q)[:K]]) for q in Q]


def prova(ef=None, usa_indice=True):
    with connection.cursor() as c:
        c.execute("SET enable_indexscan = %s" % ("on" if usa_indice else "off"))
        c.execute("SET enable_bitmapscan = %s" % ("on" if usa_indice else "off"))
        if ef:
            c.execute("SET hnsw.ef_search = %d" % ef)
        trovati, t = [], time.perf_counter()
        for q in Q:
            vett = "[" + ",".join(f"{x:.6f}" for x in q) + "]"
            c.execute(f"SELECT id FROM frasi_puntoprova ORDER BY embedding <=> '{vett}' LIMIT {K}")
            trovati.append({r[0] for r in c.fetchall()})
        ms = (time.perf_counter() - t) * 1000 / N_QUERY
    recall = np.mean([len(a & b) / K for a, b in zip(esatti, trovati)])
    return recall, ms


print(f"\n{'configurazione':<34}{'recall@10':>10}{'ms/ricerca':>12}")
r, ms = prova(usa_indice=False)
print(f"{'scansione completa (esatta)':<34}{r:>10.3f}{ms:>12.1f}")
for ef in (10, 40, 100, 200):
    r, ms = prova(ef=ef)
    etichetta = f"HNSW, ef_search = {ef}" + (" (predefinito)" if ef == 40 else "")
    print(f"{etichetta:<34}{r:>10.3f}{ms:>12.1f}")
