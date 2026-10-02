from django.db import OperationalError, connection
from django.db.migrations.executor import MigrationExecutor
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def salute(request):
    """Liveness: il processo risponde. Non tocca il database, altrimenti un guasto del database
    farebbe riavviare l'applicazione, che non risolverebbe niente."""
    return JsonResponse({"stato": "ok"})


@require_GET
def pronto(request):
    """Readiness: il database risponde e le migrazioni sono tutte applicate."""
    try:
        connection.ensure_connection()
        con = MigrationExecutor(connection)
        mancanti = con.migration_plan(con.loader.graph.leaf_nodes())
    except OperationalError:
        return JsonResponse({"stato": "database non raggiungibile"}, status=503)
    if mancanti:
        return JsonResponse({"stato": "migrazioni da applicare", "quante": len(mancanti)}, status=503)
    return JsonResponse({"stato": "pronto"})
