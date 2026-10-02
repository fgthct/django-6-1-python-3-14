from datetime import timedelta

import pytest
from django.utils import timezone

from campagne.models import Campagna, Consegna
from campagne.recupero import riaccoda_perdute

pytestmark = pytest.mark.django_db


def test_riaccoda_solo_le_consegne_in_ritardo(consegna, coda_finta):
    consegna.dovuta_il = timezone.now() - timedelta(minutes=10)
    consegna.save()
    assert riaccoda_perdute() == 1
    assert [r.kwargs for r in coda_finta.results] == [{"consegna_id": consegna.pk}]
    consegna.refresh_from_db()
    assert consegna.dovuta_il > timezone.now() - timedelta(seconds=5)  # non verrà riaccodata di nuovo subito
    assert riaccoda_perdute() == 0


def test_una_consegna_recente_non_si_tocca(consegna, coda_finta):
    consegna.dovuta_il = timezone.now() - timedelta(minutes=1)
    consegna.save()
    assert riaccoda_perdute() == 0 and coda_finta.results == []


def test_una_consegna_futura_non_si_tocca(consegna, coda_finta):
    consegna.dovuta_il = timezone.now() + timedelta(minutes=30)  # un nuovo tentativo programmato
    consegna.save()
    assert riaccoda_perdute() == 0


def test_le_consegne_chiuse_non_si_riaccodano(consegna, coda_finta):
    consegna.stato = Consegna.Stato.INVIATA
    consegna.dovuta_il = timezone.now() - timedelta(hours=1)
    consegna.save()
    assert riaccoda_perdute() == 0


def test_le_campagne_non_in_invio_non_si_riaccodano(consegna, coda_finta):
    Campagna.objects.update(stato=Campagna.Stato.COMPLETATA)
    Consegna.objects.update(dovuta_il=timezone.now() - timedelta(hours=1))
    assert riaccoda_perdute() == 0


def test_le_consegne_nascono_gia_con_una_scadenza(campagna, coda_finta):
    from campagne.models import Contatto
    from campagne.tasks import prepara_consegne

    Contatto.objects.create(email="a@example.com", nome="A")
    prepara_consegne.call(campagna_id=campagna.pk)
    assert Consegna.objects.get().dovuta_il is not None


def test_una_campagna_avviata_da_un_pezzo_e_senza_consegne_rifa_la_preparazione(campagna, coda_finta):
    campagna.avviata_il = timezone.now() - timedelta(minutes=10)
    campagna.save()
    assert riaccoda_perdute() == 1
    assert [r.kwargs for r in coda_finta.results] == [{"campagna_id": campagna.pk}]
    assert riaccoda_perdute() == 0  # la scadenza è stata aggiornata


def test_una_campagna_appena_avviata_non_si_tocca(campagna, coda_finta):
    campagna.avviata_il = timezone.now() - timedelta(seconds=30)
    campagna.save()
    assert riaccoda_perdute() == 0
