from datetime import timedelta

from django.db.models import Exists, OuterRef
from django.utils import timezone

from .models import Campagna, Consegna
from .tasks import invia_consegna, prepara_consegne


def riaccoda_perdute(oltre: timedelta = timedelta(minutes=5)) -> int:
    """Rimette in coda ciò che doveva essere partito da un pezzo e non lo è.

    Un worker ucciso a metà lavoro non avvisa nessuno: il suo task resta
    «in esecuzione» per sempre e la consegna resta «in attesa». Questa funzione
    va lanciata ogni tanto (cron, timer di systemd). È sicura: un invio che
    trova la consegna già chiusa non fa niente, e la preparazione può girare
    due volte senza danni.
    """
    limite = timezone.now() - oltre

    # 1. Campagne avviate da un pezzo che non hanno nemmeno una consegna:
    #    il task di preparazione è andato perso prima di cominciare.
    senza_consegne = Campagna.objects.filter(
        stato=Campagna.Stato.IN_INVIO, avviata_il__lt=limite
    ).exclude(Exists(Consegna.objects.filter(campagna=OuterRef("pk"))))
    campagne = list(senza_consegne.values_list("pk", flat=True))
    Campagna.objects.filter(pk__in=campagne).update(avviata_il=timezone.now())
    for pk in campagne:
        prepara_consegne.enqueue(campagna_id=pk)

    # 2. Consegne in attesa il cui momento è passato da un pezzo.
    perdute = Consegna.objects.filter(
        stato=Consegna.Stato.IN_ATTESA,
        campagna__stato=Campagna.Stato.IN_INVIO,
        dovuta_il__lt=limite,
    )
    pks = list(perdute.values_list("pk", flat=True))
    Consegna.objects.filter(pk__in=pks).update(dovuta_il=timezone.now())
    for pk in pks:
        invia_consegna.enqueue(consegna_id=pk)
    return len(campagne) + len(pks)
