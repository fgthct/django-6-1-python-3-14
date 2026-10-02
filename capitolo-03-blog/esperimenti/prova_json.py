from django.db.models import JSONNull

from articoli.models import Articolo

Articolo.objects.create(titolo="T1", slug="t1", testo="x", metadati=None)
Articolo.objects.create(titolo="T2", slug="t2", testo="x", metadati=JSONNull())
Articolo.objects.create(titolo="T3", slug="t3", testo="x", metadati={"minuti": 3})

prove = Articolo.objects.filter(slug__in=["t1", "t2", "t3"])

print("metadati__isnull=True  ->", list(prove.filter(metadati__isnull=True).values_list("slug", flat=True)))
print("metadati=JSONNull()    ->", list(prove.filter(metadati=JSONNull()).values_list("slug", flat=True)))

prove.delete()
