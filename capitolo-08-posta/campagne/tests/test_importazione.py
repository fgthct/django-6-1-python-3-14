import csv
import random
from concurrent.futures import ThreadPoolExecutor

import pytest

from campagne.importazione import importa_csv
from campagne.models import Contatto
from campagne.validazione import valida_blocco

pytestmark = pytest.mark.django_db


def scrivi(percorso, righe):
    with open(percorso, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["email", "nome"])
        w.writerows(righe)
    return percorso


RIGHE = [
    ("mario@example.com", "mario rossi"),
    ("LUCIA@Example.com", "Lucia Bianchi"),
    ("mario@example.com", "Mario di nuovo"),  # duplicato nel file
    ("rotta.example.com", "Rotta"),  # non valida
    ("anna@bücher.example", "Anna"),
]


def test_importa_conta_ogni_cosa(tmp_path):
    e = importa_csv(scrivi(tmp_path / "c.csv", RIGHE))
    assert (e.righe, e.nuovi, e.duplicati_nel_file, e.scartati, e.gia_presenti) == (5, 3, 1, 1, 0)
    assert e.esempi_scarti == ["'rotta.example.com': indirizzo non valido"]
    assert set(Contatto.objects.values_list("email", flat=True)) == {
        "mario@example.com", "lucia@example.com", "anna@xn--bcher-kva.example",
    }
    assert Contatto.objects.get(email="mario@example.com").nome == "Mario Rossi"  # vince la prima occorrenza


def test_una_seconda_importazione_non_duplica_niente(tmp_path):
    f = scrivi(tmp_path / "c.csv", RIGHE)
    importa_csv(f)
    e = importa_csv(f)
    assert (e.nuovi, e.gia_presenti) == (0, 3)
    assert Contatto.objects.count() == 3


def test_i_duplicati_a_cavallo_di_due_blocchi_si_trovano(tmp_path):
    righe = [(f"u{i}@example.com", "N") for i in range(10)] + [("u0@example.com", "N")]
    e = importa_csv(scrivi(tmp_path / "c.csv", righe), dimensione_blocco=3)
    assert (e.nuovi, e.duplicati_nel_file) == (10, 1)


def test_i_subinterpreter_danno_lo_stesso_risultato_della_serie(tmp_path):
    """La proprietà che conta: parallelizzare non cambia la risposta."""
    caso = random.Random(7)
    dom = ["example.com", "bücher.example", "città.example"]
    righe = [
        (caso.choice([f"u{caso.randrange(300)}@{caso.choice(dom)}", "rotta", " X@Y.IT "]), caso.choice(["ana", " ", "Gino  rossi"]))
        for _ in range(600)
    ]
    f = scrivi(tmp_path / "c.csv", righe)
    parallelo = importa_csv(f, dimensione_blocco=50)  # esecutore predefinito: subinterpreter
    Contatto.objects.all().delete()
    in_thread = importa_csv(f, esecutore=lambda: ThreadPoolExecutor(1), dimensione_blocco=50)
    assert parallelo == in_thread
    atteso = [e for e in valida_blocco(righe)]
    assert parallelo.scartati + parallelo.duplicati_nel_file + parallelo.nuovi == len(righe)
    assert parallelo.scartati == sum(1 for e in atteso if e[2])


def test_un_csv_vuoto(tmp_path):
    e = importa_csv(scrivi(tmp_path / "c.csv", []))
    assert e.righe == 0 and Contatto.objects.count() == 0
