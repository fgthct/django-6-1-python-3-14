from django.contrib.postgres.search import SearchQuery
from django.db import connection

from articoli.models import Articolo

query = SearchQuery("etna", config="italian", search_type="websearch")
queryset = Articolo.objects.filter(ricerca=query)

with connection.cursor() as cursore:
    # con poche righe PostgreSQL preferisce leggere tutta la tabella:
    # per vedere l'indice lo scoraggiamo, solo per questa prova
    cursore.execute("SET enable_seqscan = off")
    print(queryset.explain())
