import time
from pathlib import Path

from django.tasks import task


@task
def lavora(secondi: int) -> str:
    with open("/tmp/lavora.log", "a") as f:
        f.write(f"inizio {time.strftime('%X')}\n")
    time.sleep(secondi)
    with open("/tmp/lavora.log", "a") as f:
        f.write(f"fine   {time.strftime('%X')}\n")
    return "finito"
