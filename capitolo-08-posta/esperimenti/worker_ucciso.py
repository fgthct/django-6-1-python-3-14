"""Che cosa succede a un task se il worker muore a metà? (kill -9, cioè senza preavviso)"""
import os
import signal
import subprocess
import sys
import time

from esperimenti import prelude  # noqa: F401
from django_tasks_db.models import DBTaskResult

from esperimenti.lenta import lavora


def stato(r):
    r.refresh()
    return r.status


DBTaskResult.objects.all().delete()
open("/tmp/lavora.log", "w").close()
cmd = [sys.executable, "manage.py", "db_worker", "--no-startup-delay", "--no-reload", "--interval", "0.2"]
risultato = lavora.enqueue(secondi=6)
w = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)
print(f"dopo 2 s di lavoro      : {stato(risultato)}")
os.kill(w.pid, signal.SIGKILL)
w.wait()
print(f"worker ucciso con -9    : {stato(risultato)}")
time.sleep(1)
w2 = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(10)
print(f"10 s dopo il nuovo worker: {stato(risultato)}")
w2.terminate()
w2.wait()
print("\nregistro del task:")
print(open("/tmp/lavora.log").read())
