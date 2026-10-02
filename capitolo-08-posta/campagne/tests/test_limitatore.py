import time

from campagne import limitatore


def test_lascia_passare_fino_al_massimo_poi_ferma(redis_vero):
    nome = f"prova-{time.time_ns()}"
    ora = 1_000_000.0
    esiti = [limitatore.consenti(nome, 3, adesso=ora) for _ in range(5)]
    assert esiti == [True, True, True, False, False]


def test_la_finestra_successiva_riparte(redis_vero):
    nome = f"prova-{time.time_ns()}"
    for _ in range(3):
        limitatore.consenti(nome, 3, adesso=2_000_000.0)
    assert not limitatore.consenti(nome, 3, adesso=2_000_000.5)
    assert limitatore.consenti(nome, 3, adesso=2_000_001.0)


def test_i_nomi_sono_indipendenti(redis_vero):
    a, b = f"a-{time.time_ns()}", f"b-{time.time_ns()}"
    assert limitatore.consenti(a, 1, adesso=3_000_000.0)
    assert not limitatore.consenti(a, 1, adesso=3_000_000.0)
    assert limitatore.consenti(b, 1, adesso=3_000_000.0)


def test_i_contatori_scadono_da_soli(redis_vero):
    nome = f"prova-{time.time_ns()}"
    limitatore.consenti(nome, 1, finestra=1, adesso=4_000_000.0)
    ttl = redis_vero.ttl(f"limite:{nome}:4000000")
    assert 0 < ttl <= 2
