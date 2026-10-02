import pytest
from django.core.exceptions import ValidationError

from assistenza import servizi, tenant
from assistenza.models import Ticket
from assistenza.notifiche import notifica_nuovo_ticket

pytestmark = pytest.mark.django_db


def test_il_nuovo_ticket_avvisa_gli_admin_dopo_il_commit(acme, agente_acme, mailoutbox,
                                                         django_capture_on_commit_callbacks):
    with tenant.tenant(acme):
        with django_capture_on_commit_callbacks(execute=False) as callbacks:
            servizi.apri_ticket(agente_acme, titolo="Server giù", richiedente="c@esempio.test")
        assert mailoutbox == []  # prima del commit non parte nulla
        for callback in callbacks:
            callback()
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["admin@acme.test"]
    assert "Server giù" in mailoutbox[0].subject and "[Acme Srl]" in mailoutbox[0].subject


def test_ogni_tenant_usa_il_suo_mailer(acme, rossi, ticket_acme, ticket_rossi, mailoutbox):
    acme.mailer = "dedicato"
    acme.save()
    notifica_nuovo_ticket.call(organizzazione_id=str(acme.pk), ticket_id=str(ticket_acme.pk))
    notifica_nuovo_ticket.call(organizzazione_id=str(rossi.pk), ticket_id=str(ticket_rossi.pk))
    assert [m.sent_using for m in mailoutbox] == ["dedicato", "default"]


def test_il_task_riapre_da_solo_il_tenant(acme, ticket_acme, mailoutbox):
    """Nel worker nessun tenant è attivo: il task deve costruirselo dagli identificatori."""
    with pytest.raises(tenant.TenantMancante):
        tenant.corrente()
    assert notifica_nuovo_ticket.call(organizzazione_id=str(acme.pk), ticket_id=str(ticket_acme.pk)) == 1


def test_un_ticket_di_un_altro_tenant_non_si_puo_notificare(acme, rossi, ticket_rossi, mailoutbox):
    with pytest.raises(Ticket.DoesNotExist):
        notifica_nuovo_ticket.call(organizzazione_id=str(acme.pk), ticket_id=str(ticket_rossi.pk))
    assert mailoutbox == []


def test_un_mailer_inesistente_non_passa_la_validazione(acme):
    acme.mailer = "non-esiste"
    with pytest.raises(ValidationError):
        acme.full_clean()
    acme.mailer = "dedicato"
    acme.full_clean()


def test_senza_admin_non_parte_nulla(rossi, ticket_rossi, mailoutbox):
    rossi.membri.filter(ruolo=3).delete()
    assert notifica_nuovo_ticket.call(organizzazione_id=str(rossi.pk), ticket_id=str(ticket_rossi.pk)) == 0
    assert mailoutbox == []
