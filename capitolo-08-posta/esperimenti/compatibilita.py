"""Quali moduli si possono importare in un subinterpreter?  uso: python compatibilita.py modulo1 modulo2 ..."""
import sys
from concurrent.futures import InterpreterPoolExecutor


def prova(modulo):
    try:
        __import__(modulo)
        return "ok"
    except BaseException as errore:
        ultima_riga = [r for r in str(errore).splitlines() if r.strip()][-1:] or [""]
        return f"{type(errore).__name__}: {ultima_riga[0][:95]}"


if __name__ == "__main__":
    with InterpreterPoolExecutor(max_workers=1) as pool:
        for modulo in sys.argv[1:]:
            print(f"{modulo:<14}", pool.submit(prova, modulo).result())
