import hashlib
import hmac
import secrets

from django.db import transaction

from .models import ChiaveApi


def _impronta(testo):
    return hashlib.sha256(testo.encode()).hexdigest()


@transaction.atomic
def crea_chiave(membro):
    """Restituisce il testo della chiave: è l'unica volta in cui esiste in chiaro."""
    prefisso = secrets.token_hex(4)
    segreto = secrets.token_urlsafe(32)
    testo = f"ak_{prefisso}_{segreto}"
    ChiaveApi.objects.create(membro=membro, prefisso=prefisso, impronta=_impronta(testo))
    return testo


def verifica(testo):
    """Il Membro a cui appartiene la chiave, oppure None."""
    parti = testo.split("_", 2)
    if len(parti) != 3 or parti[0] != "ak":
        return None
    chiave = (
        ChiaveApi.objects.select_related("membro__organizzazione", "membro__user")
        .filter(prefisso=parti[1], revocata_il__isnull=True)
        .first()
    )
    if chiave is None or not hmac.compare_digest(chiave.impronta, _impronta(testo)):
        return None
    return chiave.membro
