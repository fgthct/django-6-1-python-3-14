"""Chi può fare che cosa su un documento. Un solo posto, usato da servizi e viste."""

from django.core.exceptions import PermissionDenied

from .models import Accesso

NESSUNO = 0
LETTURA = Accesso.Livello.LETTURA
MODIFICA = Accesso.Livello.MODIFICA
PROPRIETARIO = 3  # il proprietario ha un livello che nessun accesso può dare


def livello_di(utente, documento):
    if documento.proprietario_id == utente.pk:
        return PROPRIETARIO
    livello = Accesso.objects.filter(documento=documento, utente=utente).values_list("livello", flat=True).first()
    return livello or NESSUNO


def richiedi(utente, documento, minimo):
    if livello_di(utente, documento) < minimo:
        raise PermissionDenied("permesso insufficiente su questo documento")
