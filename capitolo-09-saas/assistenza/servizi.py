"""Le operazioni sui ticket. Le usano sia le viste web sia l'API: le regole stanno qui, una volta sola."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import Commento, Membro, Ticket
from .notifiche import notifica_nuovo_ticket


def richiedi(membro, ruolo_minimo):
    if not membro.puo(ruolo_minimo):
        raise PermissionDenied("ruolo insufficiente")


@transaction.atomic
def apri_ticket(membro, *, titolo, richiedente, descrizione="", priorita=Ticket.Priorita.NORMALE):
    richiedi(membro, Membro.Ruolo.AGENTE)
    ticket = Ticket.objects.create(
        titolo=titolo, richiedente=richiedente, descrizione=descrizione, priorita=priorita
    )
    # Mai accodare dentro la transazione: se facesse rollback, la notifica parlerebbe di un ticket inesistente.
    transaction.on_commit(
        lambda: notifica_nuovo_ticket.enqueue(
            organizzazione_id=str(ticket.organizzazione_id), ticket_id=str(ticket.pk)
        )
    )
    return ticket


def cambia_stato(membro, ticket, stato):
    richiedi(membro, Membro.Ruolo.AGENTE)
    if stato not in Ticket.Stato.values:
        raise ValidationError(f"stato sconosciuto: {stato}")
    ticket.stato = stato
    ticket.save(update_fields=["stato"])
    return ticket


def assegna(membro, ticket, destinatario):
    """Assegnare è da amministratori. Il destinatario deve essere della *stessa* organizzazione:
    la chiave esterna da sola non lo garantisce (non sa nulla di tenant)."""
    richiedi(membro, Membro.Ruolo.ADMIN)
    if destinatario is not None and destinatario.organizzazione_id != ticket.organizzazione_id:
        raise ValidationError("il destinatario non appartiene a questa organizzazione")
    ticket.assegnato = destinatario
    ticket.save(update_fields=["assegnato"])
    return ticket


def commenta(membro, ticket, testo):
    richiedi(membro, Membro.Ruolo.AGENTE)
    return Commento.objects.create(ticket=ticket, autore=membro, testo=testo)
