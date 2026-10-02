"""La configurazione di produzione si prova come funziona davvero: in un processo separato, con un ambiente
pulito, senza le impostazioni di sviluppo dei test."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.db import OperationalError, connection
from django.db.migrations.executor import MigrationExecutor
from django.urls import reverse

RADICE = Path(__file__).resolve().parents[2]
CHIAVE = "k7#Qe9!vT2$zLp4&Wm8*Xc1^Rn5@Yb3+Ud6-Hf0%Gj" * 2  # abbastanza lunga e varia per security.W009

PRODUZIONE = {
    "SECRET_KEY": CHIAVE,
    "ALLOWED_HOSTS": "vault.esempio.test,testserver",
    "TRUST_PROXY_SSL": "1",
    "SMTP_HOST": "posta.esempio.test",
}


def esegui(args, **ambiente):
    """Esegue Python in un processo pulito: nessuna variabile dei test, DEBUG assente (cioè produzione)."""
    env = {"PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "")}
    env.update({k: v for k, v in os.environ.items() if k.startswith("DB_")})
    env.update(ambiente)
    return subprocess.run([sys.executable, *args], cwd=RADICE, env=env, capture_output=True, text=True, timeout=120)


def impostazioni(**ambiente):
    codice = "import json, django; from django.conf import settings; print(json.dumps({'debug': settings.DEBUG}))"
    return esegui(["-c", codice], DJANGO_SETTINGS_MODULE="config.settings", **ambiente)


# --- fail closed ----------------------------------------------------------------------------------------


def test_senza_chiave_segreta_la_produzione_non_parte():
    r = impostazioni(ALLOWED_HOSTS="vault.esempio.test", SMTP_HOST="posta.esempio.test")
    assert r.returncode != 0 and "SECRET_KEY" in r.stderr


def test_senza_server_di_posta_la_produzione_non_parte():
    r = impostazioni(**{k: v for k, v in PRODUZIONE.items() if k != "SMTP_HOST"})
    assert r.returncode != 0 and "SMTP_HOST" in r.stderr


def test_senza_host_consentiti_la_produzione_non_parte():
    r = impostazioni(SECRET_KEY=CHIAVE, SMTP_HOST="posta.esempio.test")
    assert r.returncode != 0 and "ALLOWED_HOSTS" in r.stderr


def test_debug_false_e_davvero_falso():
    # Il classico errore: bool("False") è True. Qui «False» (e «off», «0», «no») spengono DEBUG.
    for valore in ("False", "off", "0", "no"):
        r = impostazioni(DEBUG=valore, **PRODUZIONE)
        assert r.returncode == 0 and json.loads(r.stdout) == {"debug": False}, valore


def test_un_valore_di_debug_incomprensibile_ferma_l_avvio():
    r = impostazioni(DEBUG="forse", **PRODUZIONE)
    assert r.returncode != 0 and "DEBUG" in r.stderr


def test_in_sviluppo_basta_dire_debug():
    r = impostazioni(DEBUG="1")
    assert r.returncode == 0 and json.loads(r.stdout) == {"debug": True}


# --- le verifiche di Django per la produzione -----------------------------------------------------------


def test_check_deploy_non_trova_niente_da_segnalare():
    r = esegui(["manage.py", "check", "--deploy", "--fail-level", "WARNING"], **PRODUZIONE)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "no issues" in r.stdout


def test_check_deploy_si_accorge_se_si_toglie_il_reindirizzamento_a_https():
    r = esegui(["manage.py", "check", "--deploy", "--fail-level", "WARNING"], SECURE_SSL_REDIRECT="0", **PRODUZIONE)
    assert r.returncode != 0 and "SECURE_SSL_REDIRECT" in (r.stdout + r.stderr)


def test_in_produzione_i_file_statici_hanno_l_impronta(tmp_path):
    r = esegui(["manage.py", "collectstatic", "--noinput"], STATIC_ROOT=str(tmp_path), **PRODUZIONE)
    assert r.returncode == 0, r.stderr
    nomi = {p.name for p in tmp_path.iterdir()}
    assert "staticfiles.json" in nomi
    assert any(n.startswith("vault.") and n.endswith(".css") and n != "vault.css" for n in nomi), nomi
    assert any(n.endswith(".gz") for n in nomi)  # e la versione compressa, pronta da servire


SCRIPT_STATICI = """
import json, django
django.setup()
from django.core.management import call_command
call_command("collectstatic", interactive=False, verbosity=0)
from django.contrib.staticfiles.storage import staticfiles_storage
from django.test import Client
nome = staticfiles_storage.stored_name("vault.css")
r = Client().get("/static/" + nome, secure=True)
print(json.dumps({"nome": nome, "stato": r.status_code, "cache": r.headers.get("Cache-Control", "")}))
"""


def test_in_produzione_i_file_statici_li_serve_l_applicazione_con_la_cache_lunga(tmp_path):
    r = esegui(
        ["-c", SCRIPT_STATICI], DJANGO_SETTINGS_MODULE="config.settings", STATIC_ROOT=str(tmp_path), **PRODUZIONE
    )
    assert r.returncode == 0, r.stderr
    ris = json.loads(r.stdout)
    assert ris["nome"] != "vault.css" and ris["stato"] == 200 and "immutable" in ris["cache"], ris


# --- HTTPS dietro il proxy ------------------------------------------------------------------------------

SCRIPT_HTTP = """
import json, django
django.setup()
from django.test import Client
c = Client()
r1 = c.get("/salute/")                                              # in HTTP, ma esente: nessun redirect
r2 = c.get("/")                                                     # in HTTP: va portato su HTTPS
r3 = c.get("/salute/", HTTP_X_FORWARDED_PROTO="https")              # il proxy dice «era HTTPS»
r4 = c.get("/", HTTP_X_FORWARDED_PROTO="https")                     # idem, su una pagina normale
print(json.dumps({
    "salute_http": r1.status_code,
    "pagina_http": [r2.status_code, r2.headers.get("Location", "")],
    "salute_https": [r3.status_code, "Strict-Transport-Security" in r3.headers],
    "pagina_https": r4.status_code,
}))
"""


def risposte(**ambiente):
    r = esegui(["-c", SCRIPT_HTTP], DJANGO_SETTINGS_MODULE="config.settings", **{**PRODUZIONE, **ambiente})
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_dietro_al_proxy_l_http_viene_portato_su_https_e_si_fida_dell_intestazione():
    ris = risposte()
    assert ris["salute_http"] == 200
    assert ris["pagina_http"][0] == 301 and ris["pagina_http"][1].startswith("https://")
    assert ris["salute_https"] == [200, True]  # HSTS presente quando la richiesta è sicura
    assert ris["pagina_https"] == 302  # niente redirect a HTTPS: arriva al login


def test_senza_fiducia_nel_proxy_l_intestazione_inviata_dal_cliente_non_conta():
    ris = risposte(TRUST_PROXY_SSL="0")
    assert ris["pagina_https"] == 301  # un cliente qualunque non può dichiararsi «già in HTTPS»


# --- liveness e readiness -------------------------------------------------------------------------------


def test_salute_non_tocca_il_database(client):
    # Senza il marcatore `django_db`, qualunque accesso al database solleva un errore: la vista non ne fa.
    assert client.get(reverse("salute")).json() == {"stato": "ok"}


@pytest.mark.django_db
def test_pronto_quando_tutto_e_a_posto(client):
    assert client.get(reverse("pronto")).json() == {"stato": "pronto"}


@pytest.mark.django_db
def test_non_pronto_se_ci_sono_migrazioni_da_applicare(client, monkeypatch):
    monkeypatch.setattr(MigrationExecutor, "migration_plan", lambda self, targets, clean_start=False: [(None, False)])
    r = client.get(reverse("pronto"))
    assert r.status_code == 503 and r.json()["stato"] == "migrazioni da applicare"


@pytest.mark.django_db
def test_non_pronto_se_il_database_non_risponde(client, monkeypatch):
    def guasto(*args, **kwargs):
        raise OperationalError("connessione rifiutata")

    monkeypatch.setattr(connection, "ensure_connection", guasto)
    r = client.get(reverse("pronto"))
    assert r.status_code == 503 and r.json()["stato"] == "database non raggiungibile"


def test_i_controlli_accettano_solo_get(client):
    assert client.post(reverse("salute")).status_code == 405
