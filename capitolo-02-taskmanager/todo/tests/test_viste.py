from django.urls import reverse

from todo.models import Attivita


def test_elenco_mostra_le_attivita(client, attivita):
    risposta = client.get(reverse("todo:elenco"))
    assert risposta.status_code == 200
    assert "Attività 2" in risposta.content.decode()


def test_elenco_e_paginato(client, attivita):
    risposta = client.get(reverse("todo:elenco"))
    assert len(risposta.context["object_list"]) == 10
    assert risposta.context["is_paginated"] is True


def test_filtro_aperte(client, attivita):
    risposta = client.get(reverse("todo:elenco"), {"stato": "aperte"})
    assert all(not a.completata for a in risposta.context["object_list"])


def test_filtro_completate(client, attivita):
    risposta = client.get(reverse("todo:elenco"), {"stato": "completate"})
    assert risposta.context["object_list"]
    assert all(a.completata for a in risposta.context["object_list"])


def test_creazione(client, progetti):
    dati = {"progetto": progetti[0].pk, "titolo": "Scrivere il capitolo", "descrizione": ""}
    risposta = client.post(reverse("todo:nuova"), dati)
    assert risposta.status_code == 302
    assert Attivita.objects.filter(titolo="Scrivere il capitolo").exists()


def test_creazione_senza_titolo_mostra_l_errore(client, progetti):
    risposta = client.post(reverse("todo:nuova"), {"progetto": progetti[0].pk, "titolo": ""})
    assert risposta.status_code == 200
    assert Attivita.objects.count() == 0


def test_modifica(client, attivita):
    a = attivita[1]
    dati = {"progetto": a.progetto_id, "titolo": "Titolo nuovo", "descrizione": ""}
    client.post(reverse("todo:modifica", args=[a.pk]), dati)
    a.refresh_from_db()
    assert a.titolo == "Titolo nuovo"


def test_completa_inverte_lo_stato(client, attivita):
    a = attivita[1]
    assert a.completata is False
    client.post(reverse("todo:completa", args=[a.pk]))
    a.refresh_from_db()
    assert a.completata is True


def test_completa_rifiuta_get(client, attivita):
    risposta = client.get(reverse("todo:completa", args=[attivita[0].pk]))
    assert risposta.status_code == 405


def test_eliminazione(client, attivita):
    a = attivita[0]
    client.post(reverse("todo:elimina", args=[a.pk]))
    assert not Attivita.objects.filter(pk=a.pk).exists()


def test_admin_elenco_attivita(admin_client, attivita):
    risposta = admin_client.get("/admin/todo/attivita/")
    assert risposta.status_code == 200
