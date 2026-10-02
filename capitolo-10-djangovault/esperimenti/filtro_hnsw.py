"""Ricerca vettoriale con un filtro di permessi: che cosa restituisce un indice HNSW?"""

import random

import numpy as np
import psycopg
from pgvector.psycopg import register_vector

DSN = "host=localhost port=5433 dbname=vault user=vault password=vault"
N, DIM, UTENTI = 30_000, 32, 100  # ogni «utente» vede l'1% delle righe

rng = np.random.default_rng(1)
with psycopg.connect(DSN, autocommit=True) as conn:
    register_vector(conn)
    conn.execute("DROP TABLE IF EXISTS prova_filtro")
    conn.execute(f"CREATE TABLE prova_filtro (id serial PRIMARY KEY, utente int NOT NULL, v vector({DIM}))")
    with conn.cursor().copy("COPY prova_filtro (utente, v) FROM STDIN WITH (FORMAT BINARY)") as copy:
        copy.set_types(["int4", "vector"])
        for i in range(N):
            copy.write_row((i % UTENTI, rng.normal(size=DIM).astype(np.float32)))
    conn.execute("CREATE INDEX ON prova_filtro USING hnsw (v vector_cosine_ops)")
    conn.execute("ANALYZE prova_filtro")

    domanda = rng.normal(size=DIM).astype(np.float32)
    sql = "SELECT id FROM prova_filtro WHERE utente = 7 ORDER BY v <=> %s LIMIT 10"

    def esegui(prefisso=""):
        with conn.transaction():
            if prefisso:
                conn.execute(prefisso)
            return [r[0] for r in conn.execute(sql, (domanda,))]

    esatti = esegui("SET LOCAL enable_indexscan = off")
    piano = [r[0].decode() if isinstance(r[0], bytes) else r[0] for r in conn.execute("EXPLAIN " + sql, (domanda,))]
    print("piano scelto dal planner:", " / ".join(riga.split("(")[0].strip(" ->") for riga in piano[:3]))
    print("risposte esatte (senza indice):         ", len(esatti))
    standard = esegui()
    print("con l'indice, impostazioni di fabbrica:  ", len(standard), "risposte,", len(set(standard) & set(esatti)), "giuste")
    for modo in ("strict_order", "relaxed_order"):
        r = esegui(f"SET LOCAL hnsw.iterative_scan = {modo}")
        print(f"con iterative_scan = {modo:14}:", len(r), "risposte,", len(set(r) & set(esatti)), "giuste")
    conn.execute("DROP TABLE prova_filtro")
