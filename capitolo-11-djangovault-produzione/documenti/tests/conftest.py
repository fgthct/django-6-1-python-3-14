import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from documenti import servizi

User = get_user_model()


@pytest.fixture(autouse=True)
def ambiente_di_prova(settings, tmp_path):
    settings.EMBEDDING_BACKEND = "finto"  # nessun modello da scaricare
    settings.MEDIA_ROOT = tmp_path / "media"  # i file dei test non finiscono mai nel progetto
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


def file_di_testo(testo="Primo paragrafo.\n\nSecondo paragrafo.", nome="nota.txt"):
    return SimpleUploadedFile(nome, testo.encode(), content_type="text/plain")


def utente(username, nome="", cognome=""):
    return User.objects.create_user(
        username, f"{username}@esempio.test", "password", first_name=nome, last_name=cognome
    )


@pytest.fixture
def marta(db):
    return utente("marta", "Marta", "Rossi")


@pytest.fixture
def luca(db):
    return utente("luca", "Luca", "Bianchi")


@pytest.fixture
def giulia(db):
    return utente("giulia", "Giulia", "Verdi")


@pytest.fixture
def paolo(db):
    return utente("paolo", "Paolo", "Neri")


@pytest.fixture
def doc(marta):
    """Un documento di Marta, in bozza, con una versione."""
    return servizi.crea_documento(marta, "Politica ferie", file_di_testo(), "Prima stesura")


def client_di(u):
    c = Client()
    c.force_login(u)
    return c
