"""Lettura delle variabili d'ambiente, con errori chiari: la configurazione sbagliata deve fermare l'avvio."""

import os

from django.core.exceptions import ImproperlyConfigured

_VERO = {"1", "true", "yes", "on"}
_FALSO = {"0", "false", "no", "off"}


def booleano(nome, predefinito):
    """`DEBUG=false` è una stringa non vuota, quindi «vera» per Python: qui la si interpreta davvero."""
    valore = os.environ.get(nome)
    if valore is None or valore.strip() == "":
        return predefinito
    chiave = valore.strip().lower()
    if chiave in _VERO:
        return True
    if chiave in _FALSO:
        return False
    raise ImproperlyConfigured(f"{nome}={valore!r} non è un booleano (usa 1/0, true/false, yes/no, on/off).")


def intero(nome, predefinito):
    valore = os.environ.get(nome)
    if valore is None or valore.strip() == "":
        return predefinito
    try:
        return int(valore)
    except ValueError:
        raise ImproperlyConfigured(f"{nome}={valore!r} non è un numero intero.") from None


def lista(nome, predefinito=()):
    valore = os.environ.get(nome, "")
    elementi = [v.strip() for v in valore.split(",") if v.strip()]
    return elementi or list(predefinito)


def obbligatoria(nome):
    valore = os.environ.get(nome, "").strip()
    if not valore:
        raise ImproperlyConfigured(f"Manca la variabile d'ambiente {nome}: in produzione è obbligatoria.")
    return valore
