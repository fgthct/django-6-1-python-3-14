from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.decorators.vary import vary_on_headers

from .forms import ContattoForm
from .models import Contatto

PER_PAGINA = 10


def contesto_elenco(request, form=None):
    q = request.GET.get("q", "").strip()
    contatti = Contatto.objects.all()
    if q:
        contatti = contatti.filter(
            Q(nome__icontains=q) | Q(email__icontains=q) | Q(citta__icontains=q)
        )
    pagina = Paginator(contatti, PER_PAGINA).get_page(request.GET.get("pagina"))
    return {
        "pagina": pagina,
        "q": q,
        "totale": Contatto.objects.count(),
        "form": form or ContattoForm(),
    }


def e_richiesta_parziale(request):
    """True se il browser vuole solo un frammento, non la pagina intera."""
    return bool(request.htmx) and not request.htmx.history_restore_request


@vary_on_headers("HX-Request")
def elenco(request):
    contesto = contesto_elenco(request)
    if e_richiesta_parziale(request):
        return render(request, "contatti/elenco.html#righe", contesto)
    return render(request, "contatti/elenco.html", contesto)


@require_GET
def conteggio(request):
    return render(request, "contatti/elenco.html#conteggio", {"totale": Contatto.objects.count()})


@require_GET
def dettaglio(request, pk):
    contatto = get_object_or_404(Contatto, pk=pk)
    return render(request, "contatti/elenco.html#dettaglio", {"contatto": contatto})


@require_GET
def riga(request, pk):
    contatto = get_object_or_404(Contatto, pk=pk)
    return render(request, "contatti/elenco.html#riga", {"contatto": contatto})


@require_http_methods(["GET", "POST"])
def modifica(request, pk):
    contatto = get_object_or_404(Contatto, pk=pk)
    if request.method == "POST":
        form = ContattoForm(request.POST, instance=contatto)
        if form.is_valid():
            contatto = form.save()
            return render(request, "contatti/elenco.html#riga", {"contatto": contatto})
    else:
        form = ContattoForm(instance=contatto)
    contesto = {"contatto": contatto, "form": form}
    return render(request, "contatti/elenco.html#riga_modifica", contesto)


@require_POST
def nuovo(request):
    form = ContattoForm(request.POST)
    if not form.is_valid():
        if request.htmx:
            return render(request, "contatti/elenco.html#form_nuovo", {"form": form})
        return render(request, "contatti/elenco.html", contesto_elenco(request, form))
    contatto = form.save()
    if not request.htmx:
        return redirect("contatti:elenco")
    contesto = {
        "contatto": contatto,
        "form": ContattoForm(),
        "totale": Contatto.objects.count(),
    }
    return render(request, "contatti/nuovo_risposta.html", contesto)


@require_http_methods(["DELETE"])
def elimina(request, pk):
    contatto = get_object_or_404(Contatto, pk=pk)
    contatto.delete()
    return HttpResponse("", headers={"HX-Trigger": "contattiCambiati"})
