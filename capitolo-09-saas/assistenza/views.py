from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import servizi
from .forms import CommentoForm, TicketForm
from .models import Membro, Ticket


def riservata(vista):
    """Serve un utente autenticato *e* un tenant: sul dominio principale non c'è nulla da vedere."""

    @login_required
    @wraps(vista)
    def interna(request, *args, **kwargs):
        if request.membro is None:
            raise Http404
        return vista(request, *args, **kwargs)

    return interna


def home(request):
    """Sul dominio principale una pagina pubblica; su un sottodominio, la dashboard."""
    if request.organizzazione is not None:
        return redirect("dashboard")
    return render(request, "assistenza/home.html")


def _contatori():
    return Ticket.objects.aggregate(
        aperti=Count("pk", filter=Q(stato=Ticket.Stato.APERTO)),
        in_lavorazione=Count("pk", filter=Q(stato=Ticket.Stato.IN_LAVORAZIONE)),
        chiusi=Count("pk", filter=Q(stato=Ticket.Stato.CHIUSO)),
    )


def _elenco(request):
    stato = request.GET.get("stato", "")
    qs = Ticket.objects.select_related("assegnato__user")
    if stato in Ticket.Stato.values:
        qs = qs.filter(stato=stato)
    pagina = Paginator(qs, 10).get_page(request.GET.get("pagina"))
    return {"pagina": pagina, "stato": stato, "stati": Ticket.Stato.choices}


@riservata
def dashboard(request):
    contesto = {"contatori": _contatori(), **_elenco(request)}
    template = "assistenza/dashboard.html"
    if request.headers.get("HX-Request") and request.headers.get("HX-Target") == "elenco":
        template += "#elenco"
    return render(request, template, contesto)


@riservata
def contatori(request):
    return render(request, "assistenza/dashboard.html#contatori", {"contatori": _contatori()})


@riservata
def nuovo(request):
    form = TicketForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ticket = servizi.apri_ticket(request.membro, **form.cleaned_data)
        return redirect("ticket", pk=ticket.pk)
    return render(request, "assistenza/nuovo.html", {"form": form})


def _ticket(pk):
    return get_object_or_404(Ticket.objects.select_related("assegnato__user"), pk=pk)


@riservata
def ticket(request, pk):
    t = _ticket(pk)
    contesto = {
        "ticket": t,
        "commenti": t.commenti.select_related("autore__user"),
        "form": CommentoForm(),
        "stati": Ticket.Stato.choices,
        "puo_scrivere": request.membro.puo(Membro.Ruolo.AGENTE),
    }
    return render(request, "assistenza/ticket.html", contesto)


@riservata
@require_POST
def cambia_stato(request, pk):
    t = _ticket(pk)
    servizi.cambia_stato(request.membro, t, request.POST.get("stato", ""))
    return render(request, "assistenza/ticket.html#stato", {"ticket": t, "stati": Ticket.Stato.choices,
                                                            "puo_scrivere": True})


@riservata
@require_POST
def commenta(request, pk):
    t = _ticket(pk)
    form = CommentoForm(request.POST)
    if not form.is_valid():
        raise PermissionDenied("commento vuoto")
    servizi.commenta(request.membro, t, form.cleaned_data["testo"])
    commenti = t.commenti.select_related("autore__user")
    return render(request, "assistenza/ticket.html#commenti", {"commenti": commenti, "ticket": t})
