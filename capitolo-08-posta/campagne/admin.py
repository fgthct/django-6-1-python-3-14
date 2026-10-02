from django.contrib import admin

from .models import Campagna, Consegna, Contatto


@admin.register(Contatto)
class ContattoAdmin(admin.ModelAdmin):
    list_display = ["email", "nome", "attivo"]
    list_filter = ["attivo"]
    search_fields = ["email", "nome"]


@admin.register(Campagna)
class CampagnaAdmin(admin.ModelAdmin):
    list_display = ["oggetto", "stato", "creata"]


@admin.register(Consegna)
class ConsegnaAdmin(admin.ModelAdmin):
    list_display = ["campagna", "contatto", "stato", "tentativi", "inviata_il"]
    list_filter = ["stato"]
    list_select_related = ["campagna", "contatto"]
