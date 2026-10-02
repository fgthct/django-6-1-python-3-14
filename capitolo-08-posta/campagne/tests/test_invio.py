import smtplib
from datetime import timedelta

import pytest
from django.utils import timezone

from campagne import tasks
from campagne.models import Campagna, Consegna, Contatto
from campagne.tasks import attesa_per_il_tentativo, invia_consegna, prepara_consegne

pytestmark = pytest.mark.django_db


def invia(consegna):
    # `.call()` esegue la funzione del task qui e ora, senza passare da nessuna coda.
    return invia_consegna.call(consegna_id=consegna.pk)


def test_invia_il_messaggio_giusto(consegna, mailoutbox, senza_limite):
    assert invia(consegna) == "inviata"
    (messaggio,) = mailoutbox
    assert messaggio.subject == "Novità d'autunno"
    assert messaggio.body == "Ciao Mario, ecco le novità."
    assert messaggio.to == ["mario@example.com"]
    assert messaggio.sent_using == "campagne"  # il mailer con nome, non quello di default
    consegna.refresh_from_db()
    assert consegna.stato == Consegna.Stato.INVIATA and consegna.inviata_il and consegna.tentativi == 1


def test_il_nome_non_e_un_modello_di_formato(consegna, mailoutbox, senza_limite):
    """Se usassimo str.format(), un testo con {nome.__class__} rivelerebbe cose che non deve."""
    consegna.campagna.corpo = "{nome.__class__} {nome}"
    consegna.campagna.save()
    invia(consegna)
    assert mailoutbox[0].body == "{nome.__class__} Mario"


def test_la_seconda_copia_del_task_non_rimanda(consegna, mailoutbox, senza_limite):
    assert invia(consegna) == "inviata"
    assert invia(consegna) == "già gestita"
    assert len(mailoutbox) == 1


def test_un_errore_smtp_programma_un_nuovo_tentativo(consegna, mailoutbox, senza_limite, coda_finta, monkeypatch, django_capture_on_commit_callbacks):
    def guasto(self, *a, **k):
        raise smtplib.SMTPServerDisconnected("connessione chiusa")

    monkeypatch.setattr("django.core.mail.message.EmailMessage.send", guasto)
    prima = timezone.now()
    with django_capture_on_commit_callbacks(execute=True):
        assert invia(consegna) == "da riprovare"
    consegna.refresh_from_db()
    assert consegna.stato == Consegna.Stato.IN_ATTESA
    assert consegna.tentativi == 1
    assert "SMTPServerDisconnected" in consegna.ultimo_errore
    (nuovo,) = coda_finta.results
    assert nuovo.kwargs == {"consegna_id": consegna.pk}
    assert prima + timedelta(seconds=9) < nuovo.task.run_after < prima + timedelta(seconds=12)


def test_dopo_l_ultimo_tentativo_la_consegna_fallisce(consegna, senza_limite, coda_finta, monkeypatch, django_capture_on_commit_callbacks):
    monkeypatch.setattr(
        "django.core.mail.message.EmailMessage.send",
        lambda self, *a, **k: (_ for _ in ()).throw(ConnectionRefusedError("rifiutata")),
    )
    consegna.tentativi = 2  # il terzo è l'ultimo
    consegna.save()
    with django_capture_on_commit_callbacks(execute=True):
        assert invia(consegna) == "fallita"
    consegna.refresh_from_db()
    assert consegna.stato == Consegna.Stato.FALLITA and consegna.tentativi == 3
    assert "ConnectionRefusedError" in consegna.ultimo_errore
    assert not coda_finta.results  # niente più tentativi
    assert Campagna.objects.get().stato == Campagna.Stato.COMPLETATA  # una consegna chiusa, anche se male


def test_il_limite_di_frequenza_rimanda_senza_consumare_un_tentativo(consegna, mailoutbox, coda_finta, monkeypatch, django_capture_on_commit_callbacks):
    monkeypatch.setattr(tasks.limitatore, "consenti", lambda *a, **k: False)
    with django_capture_on_commit_callbacks(execute=True):
        assert invia(consegna) == "rimandata"
    consegna.refresh_from_db()
    assert consegna.tentativi == 0 and consegna.stato == Consegna.Stato.IN_ATTESA
    assert not mailoutbox
    (nuovo,) = coda_finta.results
    assert nuovo.task.run_after - timezone.now() < timedelta(seconds=2)


def test_il_backoff_raddoppia():
    assert [attesa_per_il_tentativo(n).total_seconds() for n in (1, 2, 3, 4)] == [10, 20, 40, 80]


def test_la_campagna_si_chiude_solo_con_l_ultima_consegna(campagna, mailoutbox, senza_limite):
    uno = Consegna.objects.create(campagna=campagna, contatto=Contatto.objects.create(email="a@example.com", nome="A"))
    due = Consegna.objects.create(campagna=campagna, contatto=Contatto.objects.create(email="b@example.com", nome="B"))
    invia(uno)
    campagna.refresh_from_db()
    assert campagna.stato == Campagna.Stato.IN_INVIO
    invia(due)
    campagna.refresh_from_db()
    assert campagna.stato == Campagna.Stato.COMPLETATA


def test_prepara_crea_una_consegna_per_contatto_attivo(campagna, coda_finta):
    Contatto.objects.create(email="a@example.com", nome="A")
    Contatto.objects.create(email="b@example.com", nome="B", attivo=False)
    assert prepara_consegne.call(campagna_id=campagna.pk) == 1
    assert list(Consegna.objects.values_list("contatto__email", flat=True)) == ["a@example.com"]
    assert len(coda_finta.results) == 1


def test_prepara_puo_girare_due_volte(campagna, coda_finta):
    Contatto.objects.create(email="a@example.com", nome="A")
    prepara_consegne.call(campagna_id=campagna.pk)
    prepara_consegne.call(campagna_id=campagna.pk)
    assert Consegna.objects.count() == 1  # nessuna consegna doppia


def test_prepara_ignora_una_campagna_che_non_e_in_invio(campagna, coda_finta):
    campagna.stato = Campagna.Stato.BOZZA
    campagna.save()
    Contatto.objects.create(email="a@example.com", nome="A")
    assert prepara_consegne.call(campagna_id=campagna.pk) == 0
    assert Consegna.objects.count() == 0


def test_senza_destinatari_la_campagna_si_chiude_subito(campagna, coda_finta):
    assert prepara_consegne.call(campagna_id=campagna.pk) == 0
    campagna.refresh_from_db()
    assert campagna.stato == Campagna.Stato.COMPLETATA


def test_il_nuovo_tentativo_non_parte_prima_del_commit(consegna, senza_limite, coda_finta, monkeypatch):
    monkeypatch.setattr(
        "django.core.mail.message.EmailMessage.send",
        lambda self, *a, **k: (_ for _ in ()).throw(smtplib.SMTPException("no")),
    )
    invia(consegna)  # nessuna cattura dei callback: il commit non c'è stato
    assert coda_finta.results == []
