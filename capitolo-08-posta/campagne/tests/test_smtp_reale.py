"""Un vero dialogo SMTP, contro un server di prova che gira nel test (aiosmtpd)."""
import email
import email.policy
import socket

import pytest
from aiosmtpd.controller import Controller

from campagne.models import Consegna
from campagne.tasks import invia_consegna

pytestmark = pytest.mark.django_db


class Raccogli:
    def __init__(self):
        self.messaggi = []

    async def handle_DATA(self, server, session, envelope):
        self.messaggi.append((envelope.mail_from, envelope.rcpt_tos, email.message_from_bytes(envelope.content, policy=email.policy.default)))
        return "250 OK"


def porta_libera():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def server_smtp(settings):
    raccolta = Raccogli()
    porta = porta_libera()
    controller = Controller(raccolta, hostname="127.0.0.1", port=porta)
    controller.start()
    # pytest-django sostituisce ogni mailer con locmem: qui lo rimettiamo SMTP, solo per questo test
    settings.MAILERS = {
        "default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"},
        "campagne": {
            "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "OPTIONS": {"host": "127.0.0.1", "port": porta, "timeout": 5},
        },
    }
    yield raccolta
    controller.stop()


def test_il_messaggio_arriva_davvero(consegna, server_smtp, senza_limite):
    assert invia_consegna.call(consegna_id=consegna.pk) == "inviata"
    ((mittente, destinatari, msg),) = server_smtp.messaggi
    assert mittente == "campagne@bottegaetnea.example"
    assert destinatari == ["mario@example.com"]
    assert msg["Subject"] == "Novità d'autunno"  # in rete viaggia codificato; la policy moderna lo decodifica
    assert msg.get_content().strip() == "Ciao Mario, ecco le novità."


def test_con_il_server_spento_il_tentativo_viene_registrato(consegna, settings, senza_limite, coda_finta, django_capture_on_commit_callbacks):
    settings.MAILERS = {
        "default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"},
        "campagne": {
            "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "OPTIONS": {"host": "127.0.0.1", "port": porta_libera(), "timeout": 2},  # nessuno ascolta
        },
    }
    with django_capture_on_commit_callbacks(execute=True):
        assert invia_consegna.call(consegna_id=consegna.pk) == "da riprovare"
    consegna.refresh_from_db()
    assert consegna.stato == Consegna.Stato.IN_ATTESA and consegna.tentativi == 1
    assert "ConnectionRefusedError" in consegna.ultimo_errore
