from django.contrib import admin

from .models import Attivita, Progetto


@admin.register(Progetto)
class ProgettoAdmin(admin.ModelAdmin):
    search_fields = ["nome"]


@admin.register(Attivita)
class AttivitaAdmin(admin.ModelAdmin):
    list_display = ["titolo", "progetto", "completata", "scadenza"]
    list_filter = ["completata", "progetto"]
    search_fields = ["titolo", "descrizione"]
    date_hierarchy = "scadenza"
