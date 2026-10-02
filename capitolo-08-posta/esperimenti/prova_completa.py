"""Tutto insieme, con processi veri: due worker, un server SMTP, Redis, PostgreSQL.

Scenario A: 30 messaggi con il limite a 5 al secondo.
Scenario B: il server SMTP è spento all'inizio e si riaccende dopo qualche secondo.
Scenario C: un worker viene ucciso (kill -9) mentre sta inviando.
"""
import asyncio
import signal
from datetime import timedelta

import os
import socket
import subprocess
import sys
import time
from collections import Counter

from aiosmtpd.controller import Controller

from esperimenti import prelude  # noqa: F401
from django.db import connection
from django.test import Client
from django_tasks_db.models import DBTaskResult

from campagne.models import Campagna, Consegna, Contatto


class Raccogli:
    def __init__(self, lentezza=0.0):
        self.arrivi = []  # (istante, destinatario)
        self.lentezza = lentezza

    async def handle_DATA(self, server, session, envelope):
        self.arrivi.append((time.monotonic(), envelope.rcpt_tos[0]))
        await asyncio.sleep(self.lentezza)  # un server lento: lascia il tempo di uccidere un worker
        return "250 OK"


def porta_libera():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def pulisci():
    Consegna.objects.all().delete()
    Campagna.objects.all().delete()
    Contatto.objects.all().delete()
    DBTaskResult.objects.all().delete()


def avvia_worker(n, porta, extra_env):
    env = {**os.environ, "SMTP_PORT": str(porta), **extra_env}
    log = open(f"/tmp/worker{n}.log", "w")
    return subprocess.Popen(
        [sys.executable, "manage.py", "db_worker", "--no-startup-delay", "--no-reload", "--interval", "0.2"],
        env=env, stdout=log, stderr=subprocess.STDOUT,
    )


def esegui(nome, contatti, porta, extra_env, server_acceso_dopo=None):
    pulisci()
    for i in range(contatti):
        Contatto.objects.create(email=f"utente{i}@example.com", nome=f"Utente {i}")
    campagna = Campagna.objects.create(oggetto="Prova", corpo="Ciao {nome}")
    raccolta = Raccogli()
    controller = Controller(raccolta, hostname="127.0.0.1", port=porta)
    if server_acceso_dopo is None:
        controller.start()
    worker = [avvia_worker(i, porta, extra_env) for i in (1, 2)]
    t0 = time.monotonic()
    risposta = Client(HTTP_HOST="localhost").post(f"/campagne/{campagna.pk}/avvia/")
    assert risposta.status_code == 302, risposta.status_code
    avviato = server_acceso_dopo is None
    while True:
        time.sleep(0.25)
        if not avviato and time.monotonic() - t0 >= server_acceso_dopo:
            controller.start()
            avviato = True
            print(f"  [{time.monotonic() - t0:4.1f} s] il server SMTP si riaccende")
        campagna.refresh_from_db()
        if campagna.stato == Campagna.Stato.COMPLETATA or time.monotonic() - t0 > 120:
            break
    durata = time.monotonic() - t0
    for w in worker:
        w.terminate()
    for w in worker:
        w.wait()
    controller.stop()
    connection.close()

    conteggio = Counter(d for _, d in raccolta.arrivi)
    stati = Counter(Consegna.objects.values_list("stato", flat=True))
    tentativi = Counter(Consegna.objects.values_list("tentativi", flat=True))
    secondi = Counter(int(t - t0) for t, _ in raccolta.arrivi)
    print(f"== {nome}")
    print(f"  campagna {campagna.stato} in {durata:.1f} s")
    print(f"  consegne per stato: {dict(stati)}")
    print(f"  messaggi arrivati al server: {len(raccolta.arrivi)}, destinatari distinti: {len(conteggio)}, "
          f"qualcuno più di una volta: {any(v > 1 for v in conteggio.values())}")
    print(f"  tentativi per consegna: {dict(sorted(tentativi.items()))}")
    print(f"  messaggi arrivati in ciascun secondo: {dict(sorted(secondi.items()))}")


def scenario_c(porta, extra_env):
    from campagne.recupero import riaccoda_perdute

    pulisci()
    for i in range(12):
        Contatto.objects.create(email=f"utente{i}@example.com", nome=f"Utente {i}")
    campagna = Campagna.objects.create(oggetto="Prova", corpo="Ciao {nome}")
    raccolta = Raccogli(lentezza=1.0)
    controller = Controller(raccolta, hostname="127.0.0.1", port=porta)
    controller.start()
    worker = [avvia_worker(i, porta, extra_env) for i in (1, 2)]
    t0 = time.monotonic()
    Client(HTTP_HOST="localhost").post(f"/campagne/{campagna.pk}/avvia/")
    while len(raccolta.arrivi) < 2:  # i due worker hanno ciascuno un messaggio a metà
        time.sleep(0.02)
    for w in worker:
        w.send_signal(signal.SIGKILL)  # senza preavviso, mentre il server SMTP sta ancora rispondendo
    for w in worker:
        w.wait()
    print(f"  [{time.monotonic() - t0:4.1f} s] entrambi i worker uccisi con kill -9; "
          f"il server aveva già ricevuto {len(raccolta.arrivi)} messaggi")
    time.sleep(2)
    stati = Counter(Consegna.objects.values_list("stato", flat=True))
    print(f"  consegne: {dict(stati)}")
    n = riaccoda_perdute(timedelta(0))
    print(f"  riaccoda_perdute(): {n} consegne rimesse in coda")
    worker = [avvia_worker(3, porta, extra_env)]
    for _ in range(80):
        time.sleep(0.5)
        campagna.refresh_from_db()
        if campagna.stato == Campagna.Stato.COMPLETATA:
            break
    for w in worker:
        w.terminate()
    for w in worker:
        w.wait()
    controller.stop()
    connection.close()
    conteggio = Counter(d for _, d in raccolta.arrivi)
    doppi = sorted(d for d, v in conteggio.items() if v > 1)
    print("== C: worker uccisi a metà invio")
    print(f"  campagna {campagna.stato}; consegne: {dict(Counter(Consegna.objects.values_list('stato', flat=True)))}")
    print(f"  messaggi arrivati al server: {len(raccolta.arrivi)}, destinatari distinti: {len(conteggio)}")
    print(f"  destinatari che hanno ricevuto il messaggio due volte: {doppi or 'nessuno'}")


if __name__ == "__main__":
    base = {"CAMPAGNE_INVII_AL_SECONDO": "5", "CAMPAGNE_ATTESA_BASE": "2"}
    esegui("A: 30 messaggi, limite 5 al secondo", 30, porta_libera(), base)
    esegui("B: server SMTP spento per 3 secondi", 6, porta_libera(), {**base, "CAMPAGNE_INVII_AL_SECONDO": "50"}, server_acceso_dopo=3)
    scenario_c(porta_libera(), {**base, "CAMPAGNE_INVII_AL_SECONDO": "50"})
