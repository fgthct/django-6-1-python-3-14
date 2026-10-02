"""Tre modi di non trovare niente (o di trovare cose a caso) con la ricerca per parole."""
from django.contrib.postgres.search import SearchQuery

from esperimenti import prelude  # noqa: F401
from conoscenza import ricerca
from conoscenza.models import Chunk

D = "Quanti giorni di vacanza spettano in un anno?"
print("1. websearch, tutte le parole in AND :", len(ricerca.cerca_per_parole(D, 10, tutte_le_parole=True)), "risultati")
print("   websearch, parole in OR           :", len(ricerca.cerca_per_parole(D, 10)), "risultati")
print()
print("2. filter(ricerca='ferie')           :", Chunk.objects.filter(ricerca="ferie").count(), "risultati")
print("   filter(ricerca=SearchQuery(..., config='italian')):",
      Chunk.objects.filter(ricerca=SearchQuery("ferie", config="italian")).count(), "risultati")
