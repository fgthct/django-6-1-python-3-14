import pytest

from conoscenza.ricerca import fusione_rrf


def ids(fusa):
    return [e for e, _ in fusa]


def test_chi_compare_in_entrambe_vince():
    fusa = fusione_rrf([["a", "b", "c"], ["c", "d", "a"]])
    assert ids(fusa)[:2] == ["a", "c"]


def test_il_punteggio_dipende_solo_dalla_posizione():
    (_, punteggio), = fusione_rrf([["x"]], k=60)
    assert punteggio == pytest.approx(1 / 61)


def test_somma_i_contributi():
    fusa = dict(fusione_rrf([["x", "y"], ["y", "x"]], k=10))
    assert fusa["x"] == pytest.approx(1 / 11 + 1 / 12)
    assert fusa["x"] == pytest.approx(fusa["y"])


def test_a_parita_l_ordine_e_stabile():
    assert ids(fusione_rrf([["a", "b"], ["b", "a"]])) == ["a", "b"]


def test_una_classifica_vuota_non_disturba():
    assert ids(fusione_rrf([["a", "b"], []])) == ["a", "b"]
    assert fusione_rrf([]) == []


def test_k_piccolo_premia_i_primi_posti():
    # con k=1 il primo posto di una sola lista batte due terzi posti
    fusa = fusione_rrf([["solo1", "x", "y"], ["z", "w", "solo2"]], k=1)
    assert ids(fusa)[0] in ("solo1", "z")
