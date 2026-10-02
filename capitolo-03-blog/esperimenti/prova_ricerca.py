from django.contrib.postgres.search import SearchHeadline, SearchQuery, SearchRank, SearchVector
from django.db.models import F

from articoli.models import Articolo


def cerca(testo):
    query = SearchQuery(testo, config="italian", search_type="websearch")
    return (
        Articolo.objects.filter(ricerca=query)
        .annotate(rango=SearchRank(F("ricerca"), query))
        .order_by("-rango", "-pk")
    )


RICERCHE = [
    "arancine",
    "vulcano",
    "vulcani",
    "etna",
    "etna -funivia",
    '"teatro greco"',
    "lava OR ricotta",
]

for testo in RICERCHE:
    print(f"{testo!r}:")
    for a in cerca(testo):
        print(f"   {a.rango:.3f}  {a.titolo}")
