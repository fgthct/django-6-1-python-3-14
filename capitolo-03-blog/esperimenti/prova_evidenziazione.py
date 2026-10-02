from django.contrib.postgres.search import SearchHeadline, SearchQuery

from articoli.models import Articolo

query = SearchQuery("lava", config="italian", search_type="websearch")

articolo = (
    Articolo.objects.filter(ricerca=query)
    .annotate(
        estratto=SearchHeadline(
            "testo",
            query,
            config="italian",
            start_sel="⟦",
            stop_sel="⟧",
            max_words=20,
            min_words=10,
        )
    )
    .order_by("-pk")
    .first()
)

print(articolo.titolo)
print(articolo.estratto)
