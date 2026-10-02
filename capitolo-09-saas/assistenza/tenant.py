"""Il «tenant corrente»: a chi appartengono i dati di questa richiesta."""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


class TenantMancante(Exception):
    """Si è toccato un dato di un tenant senza dire quale."""


@dataclass
class Contesto:
    organizzazione: object | None = None


_contesto: ContextVar[Contesto | None] = ContextVar("contesto_tenant", default=None)


def corrente():
    contesto = _contesto.get()
    if contesto is None or contesto.organizzazione is None:
        raise TenantMancante("nessun tenant attivo: usa tenant(org) o passa dal middleware")
    return contesto.organizzazione


def corrente_o_nessuno():
    contesto = _contesto.get()
    return None if contesto is None else contesto.organizzazione


def imposta(organizzazione):
    """Sceglie il tenant dentro un contesto già aperto (lo usa l'autenticazione dell'API)."""
    contesto = _contesto.get()
    if contesto is None:
        raise TenantMancante("nessun contesto aperto")
    contesto.organizzazione = organizzazione


@contextmanager
def tenant(organizzazione=None):
    """Apre un contesto, con o senza tenant. Per middleware, task, comandi e test."""
    token = _contesto.set(Contesto(organizzazione))
    try:
        yield _contesto.get()
    finally:
        _contesto.reset(token)
