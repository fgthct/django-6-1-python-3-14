import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import ViolazioneCsp

LIMITE_CORPO = 16_000


def _tronca(valore, massimo):
    return str(valore or "")[:massimo]


@csrf_exempt  # lo invia il browser, non un nostro form: non può avere il token
@require_POST
def rapporto(request):
    if len(request.body) > LIMITE_CORPO:
        return HttpResponse(status=413)
    try:
        dati = json.loads(request.body)
    except ValueError:
        return HttpResponse(status=400)
    # Il formato storico è {"csp-report": {...}}; il nuovo (Reporting API) è una lista di rapporti.
    rapporti = dati if isinstance(dati, list) else [dati]
    salvati = []
    for voce in rapporti:
        if not isinstance(voce, dict):
            continue
        corpo = voce.get("csp-report") or voce.get("body") or {}
        if not isinstance(corpo, dict):
            continue
        salvati.append(
            ViolazioneCsp(
                host=_tronca(request.get_host(), 255),
                direttiva=_tronca(corpo.get("effective-directive") or corpo.get("effectiveDirective")
                                  or corpo.get("violated-directive"), 100),
                risorsa_bloccata=_tronca(corpo.get("blocked-uri") or corpo.get("blockedURL"), 500),
                documento=_tronca(corpo.get("document-uri") or corpo.get("documentURL"), 500),
                solo_osservazione=corpo.get("disposition") == "report",
            )
        )
    ViolazioneCsp.objects.bulk_create(salvati[:20])
    return HttpResponse(status=204)
