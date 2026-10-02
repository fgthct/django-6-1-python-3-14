import hashlib

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


def migra(bersaglio):
    esecutore = MigrationExecutor(connection)
    esecutore.migrate([bersaglio])
    return MigrationExecutor(connection).loader.project_state([bersaglio]).apps


@pytest.mark.django_db(transaction=True)
def test_la_migrazione_dei_dati_porta_il_prototipo_nel_modello_con_versioni():
    vecchio = migra(("documenti", "0001_initial"))
    Utente = vecchio.get_model("auth", "User")
    Documento = vecchio.get_model("documenti", "Documento")
    marta = Utente.objects.create(username="marta", email="m@esempio.test")
    Documento.objects.create(titolo="Politica ferie", testo="Ventisei giorni.", proprietario=marta)
    Documento.objects.create(titolo="Senza testo", testo="", proprietario=marta)

    nuovo = migra(("documenti", "0004_togli_testo_dal_documento"))
    Documento, Versione = nuovo.get_model("documenti", "Documento"), nuovo.get_model("documenti", "Versione")
    assert Documento.objects.count() == 2 and Versione.objects.count() == 2
    d = Documento.objects.get(titolo="Politica ferie")
    v = d.versione_corrente
    assert (v.numero, v.testo, v.nota, v.nome_file) == (1, "Ventisei giorni.", "Importato dal prototipo", "politica-ferie.txt")
    assert v.hash == hashlib.sha256(b"Ventisei giorni.").hexdigest()
    assert v.autore_id == d.proprietario_id and not v.file and d.stato == "bozza"


@pytest.mark.django_db(transaction=True)
def test_la_migrazione_dei_dati_si_puo_annullare_e_ripetere():
    vecchio = migra(("documenti", "0001_initial"))
    Utente = vecchio.get_model("auth", "User")
    marta = Utente.objects.create(username="marta")
    vecchio.get_model("documenti", "Documento").objects.create(titolo="D", testo="Contenuto", proprietario=marta)
    migra(("documenti", "0004_togli_testo_dal_documento"))
    indietro = migra(("documenti", "0002_versioni_revisioni_chunk"))  # annulla 0004 e 0003
    assert indietro.get_model("documenti", "Documento").objects.get().testo == "Contenuto"
    avanti = migra(("documenti", "0004_togli_testo_dal_documento"))
    assert avanti.get_model("documenti", "Versione").objects.count() == 1  # nessun duplicato


@pytest.mark.django_db(transaction=True)
def test_il_database_finale_e_quello_dei_modelli():
    migra(("documenti", "0004_togli_testo_dal_documento"))
    from django.core.management import call_command
    call_command("makemigrations", "--check", "--dry-run")
