from django.contrib import admin

from .models import Chunk, Documento


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ["titolo", "percorso", "importato_il"]
    search_fields = ["titolo"]


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ["documento", "posizione", "sezione", "modello"]
    list_select_related = ["documento"]
    exclude = ["embedding"]  # 768 numeri non servono a nessuno in un form
    readonly_fields = ["modello"]
