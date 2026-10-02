from django.core.paginator import AsyncPaginator
from django.db import transaction
from django.db.models import F, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.vary import vary_on_headers
from django_htmx.http import HttpResponseClientRedirect, trigger_client_event

from .carrello import Carrello
from .forms import OrdineForm, QuantitaForm
from .models import Categoria, Ordine, Prodotto, RigaOrdine

PER_PAGINA = 6


def e_richiesta_parziale(request):
    return bool(request.htmx) and not request.htmx.history_restore_request


@vary_on_headers("HX-Request")
async def catalogo(request):
    q = request.GET.get("q", "").strip()
    categoria = request.GET.get("categoria", "")
    prodotti = Prodotto.objects.select_related("categoria")
    if q:
        prodotti = prodotti.filter(Q(nome__icontains=q) | Q(descrizione__icontains=q))
    if categoria.isdigit():
        prodotti = prodotti.filter(categoria_id=int(categoria))

    pagina = await AsyncPaginator(prodotti, PER_PAGINA).aget_page(request.GET.get("pagina"))
    elenco = await pagina.aget_object_list()
    contesto = {
        "prodotti": elenco,
        "pagina": pagina,
        "precedente": await pagina.aprevious_page_number() if await pagina.ahas_previous() else None,
        "successiva": await pagina.anext_page_number() if await pagina.ahas_next() else None,
        "totale": await pagina.paginator.acount(),
        "q": q,
        "categoria": categoria,
        "categorie": [c async for c in Categoria.objects.all()],
        "carrello": await Carrello.da_sessione_async(request.session),
    }
    modello = "vetrina/catalogo.html#griglia" if e_richiesta_parziale(request) else "vetrina/catalogo.html"
    return render(request, modello, contesto)


def contesto_carrello(request, carrello, errore=""):
    righe = carrello.righe()
    return {"carrello": carrello, "righe": righe, "totale": carrello.totale(righe),
            "errore": errore, "form": OrdineForm()}


def risposta_carrello(request, carrello, errore=""):
    return render(request, "vetrina/carrello.html#contenuto", contesto_carrello(request, carrello, errore) | {"oob": True})


@require_GET
def carrello(request):
    c = Carrello.da_sessione(request.session)
    return render(request, "vetrina/carrello.html", contesto_carrello(request, c))


@require_POST
def aggiungi(request, pk):
    prodotto = get_object_or_404(Prodotto, pk=pk)
    c = Carrello.da_sessione(request.session)
    if c.quantita(pk) + 1 > prodotto.giacenza:
        risposta = render(request, "vetrina/base.html#badge", {"carrello": c})
        return trigger_client_event(risposta, "messaggio", {"testo": f"«{prodotto.nome}» non è più disponibile in quantità maggiore."})
    c.imposta(pk, c.quantita(pk) + 1)
    c.salva(request.session)
    risposta = render(request, "vetrina/base.html#badge", {"carrello": c})
    return trigger_client_event(risposta, "messaggio", {"testo": f"«{prodotto.nome}» aggiunto al carrello."})


@require_POST
def imposta(request, pk):
    prodotto = get_object_or_404(Prodotto, pk=pk)
    form = QuantitaForm(request.POST)
    c = Carrello.da_sessione(request.session)
    errore = ""
    if form.is_valid():
        quantita = form.cleaned_data["quantita"]
        if quantita > prodotto.giacenza:
            quantita = prodotto.giacenza
            errore = f"Di «{prodotto.nome}» ne restano solo {prodotto.giacenza}."
        c.imposta(pk, quantita)
        c.salva(request.session)
    else:
        errore = "Quantità non valida."
    return risposta_carrello(request, c, errore)


class GiacenzaInsufficiente(Exception):
    def __init__(self, prodotto):
        self.prodotto = prodotto


@require_POST
def ordina(request):
    c = Carrello.da_sessione(request.session)
    form = OrdineForm(request.POST)
    righe = c.righe()
    if not righe:
        return risposta_carrello(request, c, "Il carrello è vuoto.")
    if not form.is_valid():
        contesto = contesto_carrello(request, c) | {"form": form, "oob": True}
        return render(request, "vetrina/carrello.html#contenuto", contesto)
    try:
        with transaction.atomic():
            ordine = Ordine.objects.create(email=form.cleaned_data["email"])
            for r in righe:
                prodotto, quantita = r["prodotto"], r["quantita"]
                # L'aggiornamento condizionato è atomico: niente giacenze negative,
                # nemmeno se due clienti comprano l'ultimo pezzo nello stesso istante.
                aggiornate = Prodotto.objects.filter(pk=prodotto.pk, giacenza__gte=quantita).update(
                    giacenza=F("giacenza") - quantita
                )
                if not aggiornate:
                    raise GiacenzaInsufficiente(prodotto)
                RigaOrdine.objects.create(ordine=ordine, prodotto=prodotto, quantita=quantita,
                                          prezzo_unitario=prodotto.prezzo)
    except GiacenzaInsufficiente as e:
        return risposta_carrello(request, c, f"«{e.prodotto.nome}» non è più disponibile nella quantità richiesta.")
    request.session.pop("carrello", None)
    destinazione = reverse("vetrina:grazie", args=[ordine.pk])
    if request.htmx:
        return HttpResponseClientRedirect(destinazione)
    return redirect(destinazione)


@require_GET
def grazie(request, pk):
    ordine = get_object_or_404(Ordine.objects.prefetch_related("righe__prodotto"), pk=pk)
    return render(request, "vetrina/grazie.html", {"ordine": ordine})
