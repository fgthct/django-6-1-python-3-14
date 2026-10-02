"""Impostazioni dei test: sviluppo (DEBUG attivo) con la chiave di prova. Mai usate fuori dai test."""

import os

os.environ.setdefault("DEBUG", "1")

from .settings import *  # noqa: E402, F403
