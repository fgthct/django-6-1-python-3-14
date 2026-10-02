from esperimenti import prelude  # noqa: F401
from conoscenza import ricerca, valutazione
from conoscenza.valutazione import DOMANDE

strategie = {
    "parole": lambda q: ricerca.cerca_per_parole(q, 10),
    "parole (AND)": lambda q: ricerca.cerca_per_parole(q, 10, tutte_le_parole=True),
    "significato": lambda q: ricerca.cerca_per_significato(q, 10),
    "ibrida (AND)": lambda q: [r.chunk for r in ricerca.cerca_ibrida(q, 10)],
    "ibrida (OR)": lambda q: [r.chunk for r in ricerca.cerca_ibrida(q, 10, tutte_le_parole=False)],
}
for tipo in ("parafrasi", "esatta", None):
    gruppo = [d for d in DOMANDE if tipo is None or d.tipo == tipo]
    print(f"\n== {tipo or 'tutte'} ({len(gruppo)} domande)")
    for nome, f in strategie.items():
        p = valutazione.valuta(f, gruppo)
        print(f"{nome:12} hit@1={p.hit_1:.2f} hit@3={p.hit_3:.2f} MRR={p.mrr:.2f}")
print("\n== domande mancate")
for nome, f in strategie.items():
    for d in DOMANDE:
        pos = valutazione.posizione_della_risposta(d, list(f(d.testo)))
        if pos != 1:
            print(f"{nome:12} pos={pos}  {d.testo}")
