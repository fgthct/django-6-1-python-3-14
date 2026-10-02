"""Un limitatore di frequenza su Redis: «al massimo N invii al secondo, per tutti i worker»."""
import time
from functools import lru_cache

import redis
from django.conf import settings


@lru_cache(maxsize=1)
def _client() -> redis.Redis:
    return redis.Redis.from_url(settings.REDIS_URL, socket_timeout=2)


def consenti(nome: str, massimo: int, finestra: int = 1, *, adesso: float | None = None) -> bool:
    """True se questo invio può partire, False se la finestra corrente è già piena.

    Finestra fissa: un contatore per ogni secondo (`INCR`) che Redis cancella
    da solo (`EXPIRE`). Semplice e atomico, quindi vale per più processi
    insieme. Il suo difetto è noto: a cavallo di due finestre possono passare
    fino a 2 × massimo invii in un istante.
    """
    ora = time.time() if adesso is None else adesso
    chiave = f"limite:{nome}:{int(ora // finestra)}"
    pipe = _client().pipeline()
    pipe.incr(chiave)
    pipe.expire(chiave, finestra * 2)
    contatore, _ = pipe.execute()
    return contatore <= massimo
