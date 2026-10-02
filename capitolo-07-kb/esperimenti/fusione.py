"""Le due classifiche e la loro fusione, per una domanda."""
from esperimenti import prelude  # noqa: F401
from conoscenza.ricerca import cerca_ibrida

domanda = "Mi hanno rubato il computer, a chi telefono?"
print(f"Domanda: {domanda}\n")
print(f"{'RRF':>7}  {'signif.':>7}  {'parole':>6}  chunk")
for r in cerca_ibrida(domanda, limite=5, tutte_le_parole=False):
    s = r.posizione_significato or "—"
    p = r.posizione_parole or "—"
    print(f"{r.punteggio:7.4f}  {s!s:>7}  {p!s:>6}  {r.chunk.documento.titolo} · {r.chunk.sezione}")
