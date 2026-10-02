"""Accodare dentro una transazione: con la coda su PostgreSQL e con la coda su Redis."""
import subprocess
import sys
import time

from django.db import transaction

from esperimenti import prelude  # noqa: F401
from django_tasks_db.models import DBTaskResult

from campagne.models import Campagna
from campagne.tasks import prepara_consegne

WORKER = {
    "default": [sys.executable, "manage.py", "db_worker", "--no-startup-delay", "--no-reload", "--interval", "0.1"],
    "redis": [sys.executable, "manage.py", "rqworker", "--job-class", "django_tasks_rq.Job"],
}


def prova(backend):
    DBTaskResult.objects.all().delete()
    Campagna.objects.all().delete()
    worker = subprocess.Popen(WORKER[backend], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    with transaction.atomic():
        campagna = Campagna.objects.create(oggetto="Prova", corpo="x", stato=Campagna.Stato.IN_INVIO)
        risultato = prepara_consegne.using(backend=backend).enqueue(campagna_id=campagna.pk)  # prima del commit
        time.sleep(2)  # la transazione resta aperta: un worker veloce è già al lavoro
        durante = prepara_consegne.using(backend=backend).get_result(risultato.id).status
    time.sleep(2)
    dopo = prepara_consegne.using(backend=backend).get_result(risultato.id)
    print(f"{backend:<8} a transazione aperta: {durante:<10} dopo il commit: {dopo.status}")
    if dopo.errors:
        print("         errore:", dopo.errors[0].traceback.strip().splitlines()[-1])
    worker.terminate()
    worker.wait()


prova("default")
prova("redis")
