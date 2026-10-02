"""L'API REST, con Django Ninja. Le annotazioni sono lazy (Python 3.14): niente virgolette."""

from datetime import datetime
from uuid import UUID

from django.core.exceptions import ImproperlyConfigured, PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Schema
from ninja.pagination import LimitOffsetPagination, paginate
from ninja.responses import Status
from ninja.security import HttpBearer

from . import chiavi, servizi, tenant
from .models import Membro, Ticket


class ChiaveApiAuth(HttpBearer):
    def authenticate(self, request, token):
        membro = chiavi.verifica(token)
        if membro is None:
            return None
        # Se la richiesta arriva su un sottodominio, la chiave deve essere di *quel* tenant.
        if request.organizzazione is not None and request.organizzazione != membro.organizzazione:
            return None
        tenant.imposta(membro.organizzazione)
        request.membro = membro
        return membro


api = NinjaAPI(title="Assistenza", version="1", auth=ChiaveApiAuth(), docs_url=None)


@api.exception_handler(PermissionDenied)
def nega(request, exc):
    return api.create_response(request, {"detail": "Permesso negato"}, status=403)


@api.exception_handler(ValidationError)
def non_valido(request, exc):
    return api.create_response(request, {"detail": exc.messages}, status=422)


# Gli schemi si usano prima di essere definiti: con Python 3.14 va bene così.
class TicketOut(Schema):
    id: UUID
    titolo: str
    descrizione: str
    richiedente: str
    stato: str
    priorita: int
    assegnato: MembroOut | None
    creato: datetime


class MembroOut(Schema):
    id: int
    email: str
    ruolo: int

    @staticmethod
    def resolve_email(obj):
        return obj.user.email


class TicketIn(Schema):
    titolo: str
    richiedente: str
    descrizione: str = ""
    priorita: int = Ticket.Priorita.NORMALE


class TicketPatch(Schema):
    stato: str | None = None
    assegnato_id: int | None = None
    togli_assegnazione: bool = False


class CommentoIn(Schema):
    testo: str


class CommentoOut(Schema):
    id: UUID
    testo: str
    creato: datetime


class PaginazioneSicura(LimitOffsetPagination):
    """Come LimitOffsetPagination, ma si rifiuta di paginare un ordinamento non deterministico."""

    def paginate_queryset(self, queryset, pagination, **params):
        if hasattr(queryset, "totally_ordered") and not queryset.totally_ordered:
            raise ImproperlyConfigured(
                "Paginazione su un queryset senza ordinamento completo: pagine con righe "
                "duplicate o mancanti. Aggiungi un campo unico (es. 'pk') all'order_by."
            )
        return super().paginate_queryset(queryset, pagination, **params)


def _ticket(pk):
    return get_object_or_404(Ticket.objects.select_related("assegnato__user"), pk=pk)


@api.get("/tickets", response=list[TicketOut])
@paginate(PaginazioneSicura)
def elenco(request, stato: str | None = None):
    qs = Ticket.objects.select_related("assegnato__user")
    if stato:
        qs = qs.filter(stato=stato)
    return qs


@api.get("/tickets/{ticket_id}", response=TicketOut)
def dettaglio(request, ticket_id: UUID):
    return _ticket(ticket_id)


@api.post("/tickets", response={201: TicketOut})
def crea(request, dati: TicketIn):
    ticket = servizi.apri_ticket(request.membro, **dati.model_dump())
    return Status(201, _ticket(ticket.pk))


@api.patch("/tickets/{ticket_id}", response=TicketOut)
def aggiorna(request, ticket_id: UUID, dati: TicketPatch):
    ticket = _ticket(ticket_id)
    if dati.stato is not None:
        servizi.cambia_stato(request.membro, ticket, dati.stato)
    if dati.assegnato_id is not None or dati.togli_assegnazione:
        destinatario = None
        if dati.assegnato_id is not None:
            destinatario = get_object_or_404(
                Membro, pk=dati.assegnato_id, organizzazione=request.membro.organizzazione
            )
        servizi.assegna(request.membro, ticket, destinatario)
    return _ticket(ticket_id)


@api.post("/tickets/{ticket_id}/commenti", response={201: CommentoOut})
def commenta(request, ticket_id: UUID, dati: CommentoIn):
    return Status(201, servizi.commenta(request.membro, _ticket(ticket_id), dati.testo))
