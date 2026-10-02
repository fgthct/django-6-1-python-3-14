from articoli import signals
from articoli.models import Articolo, Commento

articolo = Articolo.objects.create(titolo="Prova", slug="prova-segnali", testo="x")
c1 = Commento.objects.create(articolo=articolo, autore="A", testo="uno")
Commento.objects.create(articolo=articolo, autore="B", testo="due")
Commento.objects.create(articolo=articolo, autore="C", testo="tre")

signals.commenti_eliminati.clear()
c1.delete()
print("dopo commento.delete():  segnali ricevuti =", len(signals.commenti_eliminati))

signals.commenti_eliminati.clear()
articolo.delete()
print("dopo articolo.delete():  segnali ricevuti =", len(signals.commenti_eliminati))
print("commenti rimasti per l'articolo:", Commento.objects.filter(articolo_id=articolo.pk).count())
