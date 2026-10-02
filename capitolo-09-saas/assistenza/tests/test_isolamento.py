import pytest
from django.apps import apps

from assistenza import tenant
from assistenza.models import Commento, ModelloDiTenant, Ticket, TenantManager
from assistenza.tenant import TenantMancante

from .conftest import crea_ticket

pytestmark = pytest.mark.django_db


def test_senza_tenant_si_fallisce_chiusi(ticket_acme):
    with pytest.raises(TenantMancante):
        Ticket.objects.all()
    with pytest.raises(TenantMancante):
        Ticket.objects.count()


def test_ogni_tenant_vede_solo_i_suoi_dati(acme, rossi, ticket_acme, ticket_rossi):
    with tenant.tenant(acme):
        assert list(Ticket.objects.values_list("titolo", flat=True)) == ["Ticket di Acme"]
    with tenant.tenant(rossi):
        assert list(Ticket.objects.values_list("titolo", flat=True)) == ["Ticket di Rossi"]


def test_l_id_di_un_altro_tenant_non_esiste(acme, ticket_rossi):
    with tenant.tenant(acme):
        assert not Ticket.objects.filter(pk=ticket_rossi.pk).exists()
        with pytest.raises(Ticket.DoesNotExist):
            Ticket.objects.get(pk=ticket_rossi.pk)


def test_il_tenant_si_imposta_da_solo_in_scrittura(acme):
    with tenant.tenant(acme):
        t = Ticket.objects.create(titolo="x", richiedente="a@b.it")
    assert t.organizzazione_id == acme.pk


def test_scrivere_su_un_altro_tenant_e_vietato(acme, rossi):
    with tenant.tenant(acme):
        with pytest.raises(PermissionError):
            Ticket.objects.create(titolo="x", richiedente="a@b.it", organizzazione=rossi)


def test_il_filtro_vale_anche_per_le_relazioni_inverse(acme, rossi, ticket_acme, agente_acme):
    with tenant.tenant(acme):
        Commento.objects.create(ticket=ticket_acme, autore=agente_acme, testo="ciao")
    with tenant.tenant(rossi):
        # Dal tenant sbagliato la relazione inversa non restituisce nulla, anche con l'oggetto in mano.
        assert ticket_acme.commenti.count() == 0
    with tenant.tenant(acme):
        assert ticket_acme.commenti.count() == 1


def test_i_contesti_si_annidano_e_si_chiudono(acme, rossi):
    with tenant.tenant(acme):
        with tenant.tenant(rossi):
            assert tenant.corrente() == rossi
        assert tenant.corrente() == acme
    with pytest.raises(TenantMancante):
        tenant.corrente()


def test_ogni_modello_con_un_tenant_usa_il_manager_che_filtra():
    """Una regola, verificata per tutti i modelli: chi aggiungerà un modello e dimenticherà il manager lo scoprirà qui."""
    globali = {"Membro", "Organizzazione", "ChiaveApi", "ViolazioneCsp"}  # fuori dal filtro, per scelta
    for modello in apps.get_app_config("assistenza").get_models():
        if modello.__name__ in globali:
            continue
        assert issubclass(modello, ModelloDiTenant), modello
        assert isinstance(modello._default_manager, TenantManager), modello


def test_i_dati_dei_test_non_si_mescolano(acme, rossi):
    crea_ticket(acme, "a")
    crea_ticket(acme, "b")
    crea_ticket(rossi, "c")
    with tenant.tenant(acme):
        assert Ticket.objects.count() == 2
    with tenant.tenant(rossi):
        assert Ticket.objects.count() == 1
