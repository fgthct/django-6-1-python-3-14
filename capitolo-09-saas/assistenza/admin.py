from django.contrib import admin

from .models import ChiaveApi, Membro, Organizzazione, Ticket, ViolazioneCsp


@admin.register(Organizzazione)
class OrganizzazioneAdmin(admin.ModelAdmin):
    list_display = ["nome", "slug", "mailer"]


@admin.register(Membro)
class MembroAdmin(admin.ModelAdmin):
    list_display = ["user", "organizzazione", "ruolo"]
    list_select_related = ["user", "organizzazione"]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """L'amministratore del *sistema* vede tutti i tenant: usa il manager senza filtro, di proposito."""

    list_display = ["titolo", "organizzazione", "stato"]
    list_select_related = ["organizzazione"]

    def get_queryset(self, request):
        return Ticket.senza_filtro.all()


admin.site.register(ChiaveApi)


@admin.register(ViolazioneCsp)
class ViolazioneCspAdmin(admin.ModelAdmin):
    list_display = ["ricevuta", "host", "direttiva", "risorsa_bloccata", "solo_osservazione"]
