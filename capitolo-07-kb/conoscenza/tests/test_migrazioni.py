import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db


def test_i_modelli_e_le_migrazioni_coincidono():
    """Se qualcuno cambia models.py senza migrazione, i test sul database non se ne accorgono."""
    call_command("makemigrations", "--check", "--dry-run", verbosity=0)
