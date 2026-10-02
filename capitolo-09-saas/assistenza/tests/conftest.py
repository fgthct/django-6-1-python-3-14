import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from assistenza import chiavi, tenant
from assistenza.models import Membro, Organizzazione, Ticket

User = get_user_model()


@pytest.fixture(autouse=True)
def fetch_raise(settings):
    """La regola di progetto: nei test, una query che ci sfugge è un errore, non un rallentamento."""
    settings.MODALITA_FETCH = "FETCH_RAISE"


@pytest.fixture(autouse=True)
def hash_veloce(settings):
    """Le password si hashano apposta lentamente; nei test, con sei utenti a ogni test, sarebbe un minuto sprecato."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


def _organizzazione(slug, nome):
    org = Organizzazione.objects.create(slug=slug, nome=nome)
    for ruolo, nome_ruolo in [(Membro.Ruolo.ADMIN, "admin"), (Membro.Ruolo.AGENTE, "agente"),
                              (Membro.Ruolo.LETTORE, "lettore")]:
        user = User.objects.create_user(f"{nome_ruolo}@{slug}.test", f"{nome_ruolo}@{slug}.test", "password")
        Membro.objects.create(user=user, organizzazione=org, ruolo=ruolo)
    return org


@pytest.fixture
def acme(db):
    return _organizzazione("acme", "Acme Srl")


@pytest.fixture
def rossi(db):
    return _organizzazione("rossi", "Studio Rossi")


def membro(org, ruolo):
    return Membro.objects.select_related("user", "organizzazione").get(organizzazione=org, ruolo=ruolo)


@pytest.fixture
def admin_acme(acme):
    return membro(acme, Membro.Ruolo.ADMIN)


@pytest.fixture
def agente_acme(acme):
    return membro(acme, Membro.Ruolo.AGENTE)


@pytest.fixture
def lettore_acme(acme):
    return membro(acme, Membro.Ruolo.LETTORE)


@pytest.fixture
def admin_rossi(rossi):
    return membro(rossi, Membro.Ruolo.ADMIN)


def crea_ticket(org, titolo="Non si accende", **extra):
    with tenant.tenant(org):
        return Ticket.objects.create(titolo=titolo, richiedente="c@esempio.test", **extra)


@pytest.fixture
def ticket_acme(acme):
    return crea_ticket(acme, "Ticket di Acme")


@pytest.fixture
def ticket_rossi(rossi):
    return crea_ticket(rossi, "Ticket di Rossi")


def client_web(org, m=None):
    c = Client(HTTP_HOST=f"{org.slug}.localhost")
    if m is not None:
        c.force_login(m.user)
    return c


def client_api(org, m):
    token = chiavi.crea_chiave(m)
    return Client(HTTP_HOST=f"{org.slug}.localhost", HTTP_AUTHORIZATION=f"Bearer {token}")
