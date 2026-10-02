from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Campagna, Consegna
from .tasks import prepara_consegne


def elenco(request):
    if request.method == "POST":
        campagna = Campagna.objects.create(
            oggetto=request.POST.get("oggetto", "").strip() or "(senza oggetto)",
            corpo=request.POST.get("corpo", ""),
        )
        return redirect("dettaglio", pk=campagna.pk)
    return render(request, "campagne/elenco.html", {"campagne": Campagna.objects.all()})


def dettaglio(request, pk):
    campagna = get_object_or_404(Campagna, pk=pk)
    return render(request, "campagne/dettaglio.html", contesto_avanzamento(campagna))


def avanzamento(request, pk):
    campagna = get_object_or_404(Campagna, pk=pk)
    return render(request, "campagne/dettaglio.html#avanzamento", contesto_avanzamento(campagna))


@require_POST
def avvia(request, pk):
    # Il passaggio bozza → in_invio è un UPDATE condizionale: se due persone
    # premono il pulsante insieme, uno solo trova ancora la bozza.
    with transaction.atomic():
        passati = Campagna.objects.filter(pk=pk, stato=Campagna.Stato.BOZZA).update(
            stato=Campagna.Stato.IN_INVIO, avviata_il=timezone.now()
        )
        if passati:
            transaction.on_commit(lambda: prepara_consegne.enqueue(campagna_id=pk))
    return redirect("dettaglio", pk=pk)


def contesto_avanzamento(campagna):
    c = campagna.consegne.aggregate(
        totale=Count("pk"),
        inviate=Count("pk", filter=Q(stato=Consegna.Stato.INVIATA)),
        fallite=Count("pk", filter=Q(stato=Consegna.Stato.FALLITA)),
        in_attesa=Count("pk", filter=Q(stato=Consegna.Stato.IN_ATTESA)),
    )
    fatte = c["inviate"] + c["fallite"]
    c["percentuale"] = round(100 * fatte / c["totale"]) if c["totale"] else 0
    return {"campagna": campagna, "conteggi": c}
