from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404

from . import tenant
from .models import Membro, Organizzazione


def sottodominio(host):
    """'acme.localhost:8000' → 'acme'; 'localhost' → None."""
    nome = host.split(":")[0].lower()
    base = settings.DOMINIO_BASE
    if nome.endswith("." + base):
        return nome.removesuffix("." + base) or None
    return None


class TenantMiddleware:
    """Dal sottodominio all'organizzazione, per tutta la durata della richiesta."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.organizzazione = None
        request.membro = None
        slug = sottodominio(request.get_host())
        with tenant.tenant() as contesto:
            if slug is not None:
                try:
                    organizzazione = Organizzazione.objects.get(slug=slug)
                except Organizzazione.DoesNotExist:
                    raise Http404("Organizzazione sconosciuta") from None
                contesto.organizzazione = request.organizzazione = organizzazione
                if request.user.is_authenticated:
                    try:
                        request.membro = Membro.objects.select_related("user").get(
                            user=request.user, organizzazione=organizzazione
                        )
                    except Membro.DoesNotExist:
                        raise PermissionDenied("Non sei un membro di questa organizzazione") from None
            return self.get_response(request)
