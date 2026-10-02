"""Il ciclo di vita di un task: READY → (worker) → SUCCESSFUL o FAILED. E nessun nuovo tentativo."""
import subprocess
import sys

from django.tasks import default_task_backend  # noqa: F401
from django.test.utils import override_settings

from esperimenti import prelude  # noqa: F401
from esperimenti.esempi import fallisce, somma

# 1. ImmediateBackend: il backend predefinito dei nuovi progetti. Niente coda, niente worker.
with override_settings(TASKS={"default": {"BACKEND": "django.tasks.backends.immediate.ImmediateBackend"}}):
    r = somma.enqueue(2, 3)
    print(f"Immediate : subito dopo enqueue → {r.status}, return_value={r.return_value}")

# 2. Il backend su PostgreSQL: il task aspetta un worker.
ok = somma.enqueue(2, 3)
ko = fallisce.enqueue()
print(f"PostgreSQL: subito dopo enqueue → {ok.status}")
subprocess.run([sys.executable, "manage.py", "db_worker", "--batch", "--no-startup-delay", "--no-reload"],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
ok = somma.get_result(ok.id)
ko = fallisce.get_result(ko.id)
print(f"            dopo il worker  → {ok.status}, return_value={ok.return_value}")
print(f"            task fallito    → {ko.status}, errori: {len(ko.errors)}, "
      f"ultima riga: {ko.errors[0].traceback.strip().splitlines()[-1]}")
print(f"            tentativi fatti: {ko.attempts} (nessun nuovo tentativo automatico)")
