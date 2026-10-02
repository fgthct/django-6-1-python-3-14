from django.conf import settings
from django.core.mail import EmailMessage
from django.tasks import task

from . import tenant
from .models import Membro, Organizzazione, Ticket


@task
def notifica_nuovo_ticket(organizzazione_id, ticket_id):
    """Avvisa gli amministratori. Un task non vive dentro la richiesta: il tenant
    non c'è, e va riaperto a partire dall'identificatore che ci è stato passato."""
    organizzazione = Organizzazione.objects.get(pk=organizzazione_id)
    with tenant.tenant(organizzazione):
        ticket = Ticket.objects.get(pk=ticket_id)
        destinatari = list(
            Membro.objects.filter(organizzazione=organizzazione, ruolo=Membro.Ruolo.ADMIN)
            .select_related("user")
            .values_list("user__email", flat=True)
        )
        if not destinatari:
            return 0
        EmailMessage(
            subject=f"[{organizzazione.nome}] Nuovo ticket: {ticket.titolo}",
            body=f"{ticket.richiedente} ha aperto un ticket.\n\n{ticket.descrizione}",
            from_email=settings.EMAIL_DA,
            to=destinatari,
        ).send(using=organizzazione.mailer)
        return len(destinatari)
