from django.core.exceptions import FieldFetchBlocked
from django.db import connection, models
from django.test.utils import CaptureQueriesContext

from todo.models import Attivita


def misura(descrizione, queryset):
    with CaptureQueriesContext(connection) as contesto:
        nomi = [a.progetto.nome for a in queryset]
    print(f"{descrizione:<28} {len(nomi)} righe -> {len(contesto):>2} query")


misura("FETCH_ONE (predefinito)", Attivita.objects.all())
misura("FETCH_PEERS", Attivita.objects.fetch_mode(models.FETCH_PEERS))
misura("select_related", Attivita.objects.select_related("progetto"))

try:
    [a.progetto.nome for a in Attivita.objects.fetch_mode(models.FETCH_RAISE)]
except FieldFetchBlocked as errore:
    print("FETCH_RAISE:", errore)
