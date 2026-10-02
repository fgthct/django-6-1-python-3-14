from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import permessi, servizi
from .forms import (AccessoForm, DecisioneForm, DomandaForm, NuovaVersioneForm, NuovoDocumentoForm,
                    RevisioneForm)
from .models import Documento, Partecipante, Revisione
from .rag import rispondi
from .ricerca import cerca
from .servizi import ErroreDiDominio


def _documento(request, pk):
    """Un documento *che l'utente può vedere*: gli altri, per lui, non esistono (404, non 403)."""
    visibili = Documento.objects.visibili_a(request.user).select_related("proprietario", "versione_corrente")
    return get_object_or_404(visibili, pk=pk)


def _esegui(request, azione, *args, ok=None, **kwargs):
    """Chiama un servizio e trasforma gli errori di dominio in messaggi per l'utente."""
    try:
        risultato = azione(request.user, *args, **kwargs)
    except ErroreDiDominio as errore:
        messages.error(request, str(errore))
        return None
    if ok:
        messages.success(request, ok)
    return risultato if risultato is not None else True


@login_required
def elenco(request):
    documenti = Documento.objects.visibili_a(request.user).select_related("proprietario", "versione_corrente")
    return render(request, "documenti/elenco.html", {"documenti": documenti, "form": NuovoDocumentoForm(),
                                                       "domanda": DomandaForm()})


@login_required
@require_POST
def nuovo(request):
    form = NuovoDocumentoForm(request.POST, request.FILES)
    if form.is_valid():
        documento = _esegui(request, servizi.crea_documento, form.cleaned_data["titolo"], form.cleaned_data["file"],
                            form.cleaned_data["nota"], ok="Documento creato.")
        if documento:
            return redirect("dettaglio", pk=documento.pk)
    else:
        messages.error(request, "Titolo e file sono obbligatori.")
    return redirect("elenco")


def _flusso(request, documento):
    revisione = (documento.revisioni.filter(stato=Revisione.Stato.APERTA)
                 .prefetch_related("partecipanti__utente").first())
    conclusa = None
    if revisione is None:
        conclusa = documento.revisioni.exclude(stato=Revisione.Stato.APERTA).prefetch_related("partecipanti__utente").first()
    tocca_a_me = False
    if revisione:
        in_attesa = [p for p in revisione.partecipanti.all() if p.decisione == Partecipante.Decisione.IN_ATTESA]
        if revisione.modalita == Revisione.Modalita.IN_SEQUENZA:
            tocca_a_me = bool(in_attesa) and in_attesa[0].utente_id == request.user.pk
        else:
            tocca_a_me = any(p.utente_id == request.user.pk for p in in_attesa)
    return {
        "documento": documento, "revisione": revisione, "conclusa": conclusa, "tocca_a_me": tocca_a_me,
        "livello": permessi.livello_di(request.user, documento), "PROPRIETARIO": permessi.PROPRIETARIO,
        "eventi": documento.eventi.select_related("utente")[:12], "decisione": DecisioneForm(),
        "revisione_form": RevisioneForm(proprietario=documento.proprietario),
    }


@login_required
def dettaglio(request, pk):
    documento = _documento(request, pk)
    contesto = _flusso(request, documento)
    contesto.update(
        versioni=documento.versioni.select_related("autore"),
        accessi=documento.accessi.select_related("utente"),
        versione_form=NuovaVersioneForm(),
        accesso_form=AccessoForm(proprietario=documento.proprietario),
    )
    return render(request, "documenti/dettaglio.html", contesto)


def _risposta_flusso(request, documento):
    """Dopo un'azione: ai browser HTMX il solo frammento del flusso, agli altri un redirect."""
    if request.headers.get("HX-Request"):
        documento = _documento(request, documento.pk)
        contesto = _flusso(request, documento)
        # Con HTMX la pagina non si ricarica: i messaggi (anche gli errori!) devono stare nel frammento.
        contesto["avvisi"] = list(messages.get_messages(request))
        return render(request, "documenti/dettaglio.html#flusso", contesto)
    return redirect("dettaglio", pk=documento.pk)


@login_required
@require_POST
def nuova_versione(request, pk):
    documento = _documento(request, pk)
    form = NuovaVersioneForm(request.POST, request.FILES)
    if form.is_valid():
        _esegui(request, servizi.carica_versione, documento, form.cleaned_data["file"], form.cleaned_data["nota"],
                ok="Nuova versione caricata.")
    else:
        messages.error(request, "Scegli un file.")
    return redirect("dettaglio", pk=pk)


@login_required
@require_POST
def invia_revisione(request, pk):
    documento = _documento(request, pk)
    form = RevisioneForm(request.POST, proprietario=documento.proprietario)
    if form.is_valid():
        _esegui(request, servizi.invia_in_revisione, documento, form.revisori(), form.cleaned_data["modalita"],
                form.cleaned_data["messaggio"], ok="Documento inviato in revisione.")
    else:
        messages.error(request, "Scegli almeno un revisore e una modalità.")
    return _risposta_flusso(request, documento)


@login_required
@require_POST
def decidi(request, pk):
    documento = _documento(request, pk)
    approva = request.POST.get("esito") == "approva"
    commento = request.POST.get("commento", "")
    _esegui(request, servizi.decidi, documento, approva, commento,
            ok="Approvazione registrata." if approva else "Documento rimandato in bozza.")
    return _risposta_flusso(request, documento)


@login_required
@require_POST
def annulla(request, pk):
    documento = _documento(request, pk)
    _esegui(request, servizi.annulla_revisione, documento, ok="Revisione annullata.")
    return _risposta_flusso(request, documento)


@login_required
@require_POST
def accesso(request, pk):
    documento = _documento(request, pk)
    form = AccessoForm(request.POST, proprietario=documento.proprietario)
    if form.is_valid():
        _esegui(request, servizi.concedi_accesso, documento, form.cleaned_data["utente"], form.cleaned_data["livello"],
                ok="Accesso concesso.")
    return redirect("dettaglio", pk=pk)


@login_required
@require_POST
def revoca(request, pk, utente_id):
    documento = _documento(request, pk)
    destinatario = get_object_or_404(documento.accessi.select_related("utente"), utente_id=utente_id).utente
    _esegui(request, servizi.revoca_accesso, documento, destinatario, ok="Accesso revocato.")
    return redirect("dettaglio", pk=pk)


@login_required
def scarica(request, pk, numero):
    """I file non hanno un indirizzo pubblico: passano da qui, dopo il controllo dei permessi."""
    documento = _documento(request, pk)
    versione = get_object_or_404(documento.versioni, numero=numero)
    if versione.file:
        return FileResponse(versione.file.open("rb"), as_attachment=True, filename=versione.nome_file)
    risposta = HttpResponse(versione.testo, content_type="text/plain; charset=utf-8")
    risposta["Content-Disposition"] = f'attachment; filename="{versione.nome_file}"'
    return risposta


@login_required
def cerca_vista(request):
    form = DomandaForm(request.GET)
    risultati = cerca(request.user, form.cleaned_data["q"]) if form.is_valid() else []
    return render(request, "documenti/elenco.html#risultati", {"risultati": risultati, "q": request.GET.get("q", "")})


@login_required
@require_POST
def chiedi(request):
    form = DomandaForm(request.POST)
    if not form.is_valid():
        raise Http404
    return render(request, "documenti/elenco.html#risposta", {"risposta": rispondi(request.user, form.cleaned_data["q"])})
