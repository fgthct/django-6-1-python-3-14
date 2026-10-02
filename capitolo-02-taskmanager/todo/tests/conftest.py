import pytest

from todo.models import Attivita, Progetto


@pytest.fixture
def progetti(db):
    return [Progetto.objects.create(nome=nome) for nome in ("Casa", "Lavoro", "Libro")]


@pytest.fixture
def attivita(progetti):
    return [
        Attivita.objects.create(
            progetto=progetti[i % 3],
            titolo=f"Attività {i + 1}",
            completata=(i % 4 == 0),
        )
        for i in range(12)
    ]
