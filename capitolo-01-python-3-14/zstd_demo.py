import json

from compression import zstd

articoli = [
    {"id": i, "titolo": f"Articolo {i}", "testo": "Lorem ipsum dolor sit amet " * 5}
    for i in range(1000)
]
dati = json.dumps(articoli).encode()

compresso = zstd.compress(dati, level=9)
print(f"{len(dati)} -> {len(compresso)} byte")

assert zstd.decompress(compresso) == dati
