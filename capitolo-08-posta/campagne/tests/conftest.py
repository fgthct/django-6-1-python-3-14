import pytest
import redis as redis_py
from django.conf import settings

from campagne.models import Campagna, Consegna, Contatto


@pytest.fixture
def coda_finta(settings):
    """Una coda che non esegue niente e ricorda tutto: ci permette di guardare cosa viene accodato."""
    settings.TASKS = {"default": {"BACKEND": "django.tasks.backends.dummy.DummyBackend"}}
    from django.tasks import default_task_backend

    default_task_backend.clear()
    yield default_task_backend
    default_task_backend.clear()


@pytest.fixture
def senza_limite(monkeypatch):
    """Per i test che non parlano del limitatore: il via libera è sempre concesso."""
    from campagne import limitatore

    monkeypatch.setattr(limitatore, "consenti", lambda *a, **k: True)


@pytest.fixture
def redis_vero():
    client = redis_py.Redis.from_url(settings.REDIS_URL, socket_timeout=1)
    try:
        client.ping()
    except redis_py.exceptions.RedisError:
        pytest.skip("Redis non raggiungibile")
    return client


@pytest.fixture
def campagna(db):
    return Campagna.objects.create(
        oggetto="Novità d'autunno", corpo="Ciao {nome}, ecco le novità.", stato=Campagna.Stato.IN_INVIO
    )


@pytest.fixture
def consegna(campagna):
    contatto = Contatto.objects.create(email="mario@example.com", nome="Mario")
    return Consegna.objects.create(campagna=campagna, contatto=contatto)
