from todo.models import Attivita


def test_str(progetti):
    assert str(progetti[0]) == "Casa"


def test_ordinamento_predefinito_e_deterministico(db):
    assert Attivita.objects.all().totally_ordered is True


def test_ordinamento_senza_campo_unico_non_e_deterministico(db):
    queryset = Attivita.objects.order_by("completata", "-creata")
    assert queryset.totally_ordered is False


def test_aggiungere_la_chiave_primaria_rende_deterministico(db):
    queryset = Attivita.objects.order_by("completata", "-creata", "pk")
    assert queryset.totally_ordered is True


def test_le_aperte_vengono_prima_delle_completate(attivita):
    stati = [a.completata for a in Attivita.objects.all()]
    assert stati == sorted(stati)
