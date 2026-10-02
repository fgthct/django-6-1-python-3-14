"""Quattro modi di validare lo stesso CSV: in serie, con thread, con processi, con subinterpreter."""
import os
import sys
import time
from concurrent.futures import InterpreterPoolExecutor, ProcessPoolExecutor, ThreadPoolExecutor
from itertools import batched
from pathlib import Path

from campagne.validazione import valida_blocco
from esperimenti.genera_csv import genera


class InSerie:
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def map(self, f, it): return map(f, it)


def leggi(percorso):
    import csv
    with open(percorso, newline="", encoding="utf-8") as f:
        return [(r["email"], r["nome"]) for r in csv.DictReader(f)]


def misura(fabbrica, blocchi, ripetizioni=3):
    tempi = []
    for _ in range(ripetizioni):
        t0 = time.perf_counter()
        with fabbrica() as pool:
            sum(len(x) for x in pool.map(valida_blocco, blocchi))
        tempi.append(time.perf_counter() - t0)
    return tempi


if __name__ == "__main__":
    percorso = Path(sys.argv[1])
    righe = leggi(percorso)
    blocchi = [list(b) for b in batched(righe, 5000)]
    print(f"{len(righe)} righe in {len(blocchi)} blocchi, {os.cpu_count()} core, tre prove ciascuno\n")
    print(f"{'modo':<18}{'prove (s)':<22}{'migliore':>9}{'rispetto alla serie':>22}")
    base = None
    for nome, f in [
        ("in serie", InSerie),
        ("2 thread", lambda: ThreadPoolExecutor(2)),
        ("2 processi", lambda: ProcessPoolExecutor(2)),
        ("2 subinterpreter", lambda: InterpreterPoolExecutor(2)),
    ]:
        t = misura(f, blocchi)
        base = base or min(t)
        prove = " ".join(f"{x:.2f}" for x in t)
        print(f"{nome:<18}{prove:<22}{min(t):>8.2f}s{base / min(t):>21.2f}x")
