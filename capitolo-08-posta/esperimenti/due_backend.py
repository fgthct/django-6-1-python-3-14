"""Lo stesso task su due code: PostgreSQL (django-tasks-db) e Redis (django-tasks-rq)."""
import subprocess
import sys
import time
from datetime import timedelta

from django.tasks import task_backends
from django.utils import timezone

from esperimenti import prelude  # noqa: F401
from esperimenti.lenta import lavora

WORKER = {
    "default": [sys.executable, "manage.py", "db_worker", "--batch", "--no-startup-delay", "--no-reload"],
    "redis": [sys.executable, "manage.py", "rqworker", "--job-class", "django_tasks_rq.Job", "--burst"],
}

print(f"{'':<34}{'PostgreSQL':<14}{'Redis (RQ)':<14}")
for caratteristica in ("supports_defer", "supports_priority", "supports_get_result", "supports_async_task"):
    valori = [getattr(task_backends[nome], caratteristica) for nome in ("default", "redis")]
    print(f"{caratteristica:<34}{valori[0]!s:<14}{valori[1]!s:<14}")

risultati = {}
for nome in ("default", "redis"):
    t = lavora.using(backend=nome, priority=10 if nome == "default" else 0)
    risultati[nome] = (t.enqueue(secondi=1), time.monotonic())

print()
for nome in ("default", "redis"):
    r, t0 = risultati[nome]
    print(f"{nome:<8} subito dopo enqueue: {r.status}")
    subprocess.run(WORKER[nome], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    r = lavora.using(backend=nome).get_result(r.id)
    print(f"{nome:<8} dopo il worker     : {r.status}, return_value={r.return_value!r}")
