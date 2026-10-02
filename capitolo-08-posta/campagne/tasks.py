import smtplib
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.tasks import task
from django.utils import timezone

from . import limitatore
from .models import Campagna, Consegna, Contatto


def attesa_per_il_tentativo(tentativo: int) -> timedelta:
    """Backoff esponenziale: 10 s, 20 s, 40 s… (la base sta nelle impostazioni)."""
    return timedelta(seconds=settings.CAMPAGNE_ATTESA_BASE * 2 ** (tentativo - 1))


@task
def prepara_consegne(campagna_id: int) -> int:
    """Crea una Consegna per ogni contatto attivo e accoda un invio per ciascuna.

    Può girare due volte (una coda consegna *almeno una volta*, non *esattamente
    una*): per questo `ignore_conflicts` e l'invio che guarda lo stato.
    """
    campagna = Campagna.objects.get(pk=campagna_id)
    if campagna.stato != Campagna.Stato.IN_INVIO:
        return 0
    Consegna.objects.bulk_create(
        [
            Consegna(campagna=campagna, contatto=c, dovuta_il=timezone.now())
            for c in Contatto.objects.filter(attivo=True)
        ],
        ignore_conflicts=True,
    )
    in_attesa = campagna.consegne.filter(stato=Consegna.Stato.IN_ATTESA)
    da_inviare = list(in_attesa.values_list("pk", flat=True))
    in_attesa.update(dovuta_il=timezone.now())
    for pk in da_inviare:
        invia_consegna.enqueue(consegna_id=pk)
    _chiudi_se_finita(campagna_id)  # nessun contatto attivo: finita subito
    return len(da_inviare)


@task
def invia_consegna(consegna_id: int) -> str:
    """Invia un messaggio. Restituisce che cosa è successo, come testo."""
    with transaction.atomic():
        consegna = (
            Consegna.objects.select_for_update()
            .select_related("campagna", "contatto")
            .get(pk=consegna_id)
        )
        # 1. Un'altra copia del task può averla già chiusa.
        if consegna.stato != Consegna.Stato.IN_ATTESA:
            return "già gestita"

        # 2. Un limite di frequenza comune a tutti i worker.
        if not limitatore.consenti("campagne", settings.CAMPAGNE_INVII_AL_SECONDO):
            _riprova(consegna_id, timedelta(seconds=1))
            return "rimandata"

        # 3. L'invio vero.
        corpo = consegna.campagna.corpo.replace("{nome}", consegna.contatto.nome)
        messaggio = EmailMessage(
            subject=consegna.campagna.oggetto,
            body=corpo,
            from_email=settings.CAMPAGNE_MITTENTE,
            to=[consegna.contatto.email],
        )
        consegna.tentativi += 1
        try:
            messaggio.send(using="campagne")
        except (smtplib.SMTPException, OSError) as errore:
            consegna.ultimo_errore = f"{type(errore).__name__}: {errore}"
            if consegna.tentativi >= settings.CAMPAGNE_MAX_TENTATIVI:
                consegna.stato = Consegna.Stato.FALLITA
                esito = "fallita"
            else:
                _riprova(consegna_id, attesa_per_il_tentativo(consegna.tentativi))
                esito = "da riprovare"
        else:
            consegna.stato = Consegna.Stato.INVIATA
            consegna.inviata_il = timezone.now()
            consegna.ultimo_errore = ""
            esito = "inviata"
        consegna.save()
    _chiudi_se_finita(consegna.campagna_id)
    return esito


def _riprova(consegna_id: int, attesa: timedelta) -> None:
    # Il nuovo task parte solo dopo il commit: altrimenti un worker veloce
    # potrebbe leggere la riga prima che questa transazione l'abbia aggiornata.
    quando = timezone.now() + attesa
    Consegna.objects.filter(pk=consegna_id).update(dovuta_il=quando)
    transaction.on_commit(lambda: invia_consegna.using(run_after=quando).enqueue(consegna_id=consegna_id))


def _chiudi_se_finita(campagna_id: int) -> None:
    ancora_in_attesa = Exists(
        Consegna.objects.filter(campagna=OuterRef("pk"), stato=Consegna.Stato.IN_ATTESA)
    )
    Campagna.objects.filter(pk=campagna_id, stato=Campagna.Stato.IN_INVIO).exclude(
        ancora_in_attesa
    ).update(stato=Campagna.Stato.COMPLETATA)


@task
def importa_contatti(percorso: str) -> dict:
    """L'importazione di un CSV, in background (il risultato deve essere JSON)."""
    from dataclasses import asdict
    from pathlib import Path

    from .importazione import importa_csv

    return asdict(importa_csv(Path(percorso)))
