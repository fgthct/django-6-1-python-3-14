import pytest
from django.core.exceptions import ImproperlyConfigured

from config import ambiente


@pytest.mark.parametrize("valore", ["1", "true", "True", "YES", "on", " 1 "])
def test_booleano_vero(monkeypatch, valore):
    monkeypatch.setenv("X", valore)
    assert ambiente.booleano("X", False) is True


@pytest.mark.parametrize("valore", ["0", "false", "False", "NO", "off"])
def test_booleano_falso(monkeypatch, valore):
    monkeypatch.setenv("X", valore)
    assert ambiente.booleano("X", True) is False


def test_booleano_assente_o_vuoto_usa_il_predefinito(monkeypatch):
    monkeypatch.delenv("X", raising=False)
    assert ambiente.booleano("X", True) is True
    monkeypatch.setenv("X", "  ")
    assert ambiente.booleano("X", False) is False


def test_booleano_incomprensibile_e_un_errore(monkeypatch):
    monkeypatch.setenv("X", "forse")
    with pytest.raises(ImproperlyConfigured, match="X='forse'"):
        ambiente.booleano("X", False)


def test_intero(monkeypatch):
    monkeypatch.setenv("N", "42")
    assert ambiente.intero("N", 1) == 42
    monkeypatch.delenv("N")
    assert ambiente.intero("N", 7) == 7
    monkeypatch.setenv("N", "quaranta")
    with pytest.raises(ImproperlyConfigured, match="intero"):
        ambiente.intero("N", 1)


def test_lista_toglie_spazi_e_vuoti(monkeypatch):
    monkeypatch.setenv("L", " a.test, b.test ,, ")
    assert ambiente.lista("L") == ["a.test", "b.test"]
    monkeypatch.delenv("L")
    assert ambiente.lista("L", ["x"]) == ["x"]


def test_obbligatoria(monkeypatch):
    monkeypatch.setenv("O", "  valore ")
    assert ambiente.obbligatoria("O") == "valore"
    monkeypatch.setenv("O", " ")
    with pytest.raises(ImproperlyConfigured, match="O"):
        ambiente.obbligatoria("O")
