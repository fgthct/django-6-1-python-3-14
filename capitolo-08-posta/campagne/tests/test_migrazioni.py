import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db


def test_i_modelli_e_le_migrazioni_coincidono():
    call_command("makemigrations", "--check", "--dry-run", verbosity=0)
