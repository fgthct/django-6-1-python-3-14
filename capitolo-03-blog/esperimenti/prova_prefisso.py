from django.contrib.postgres.search import Lexeme, SearchQuery

from articoli.models import Articolo

query = SearchQuery(Lexeme("vulc", prefix=True), config="italian", search_type="raw")

for articolo in Articolo.objects.filter(ricerca=query):
    print(articolo.titolo)
