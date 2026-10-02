import pytest
from django.core.exceptions import FieldFetchBlocked
from django.db import connection, models
from django.test.utils import CaptureQueriesContext

from todo.models import Attivita


def conta_query(modo):
    with CaptureQueriesContext(connection) as contesto:
        nomi = [a.progetto.nome for a in Attivita.objects.fetch_mode(modo)]
    return len(nomi), len(contesto)


def test_fetch_one_produce_il_problema_n_piu_1(attivita):
    righe, query = conta_query(models.FETCH_ONE)
    assert righe == 12
    assert query == 1 + 12


def test_fetch_peers_risolve_con_due_query(attivita):
    righe, query = conta_query(models.FETCH_PEERS)
    assert righe == 12
    assert query == 2


def test_fetch_raise_fa_emergere_il_problema(attivita):
    with pytest.raises(FieldFetchBlocked):
        [a.progetto.nome for a in Attivita.objects.fetch_mode(models.FETCH_RAISE)]


def test_fetch_raise_non_blocca_con_select_related(attivita):
    queryset = Attivita.objects.select_related("progetto")
    nomi = [a.progetto.nome for a in queryset.fetch_mode(models.FETCH_RAISE)]
    assert len(nomi) == 12


def test_pagina_elenco_ha_un_numero_fisso_di_query(client, attivita, django_assert_num_queries):
    with django_assert_num_queries(3):   # conteggio, pagina, progetti
        risposta = client.get("/")
    assert risposta.status_code == 200
