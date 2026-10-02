from django.contrib import admin

from .models import Articolo, Categoria, Commento


class CommentoInline(admin.TabularInline):
    model = Commento
    extra = 0


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("nome",)}


@admin.register(Articolo)
class ArticoloAdmin(admin.ModelAdmin):
    list_display = ["titolo", "categoria", "pubblicato", "pubblicato_il"]
    list_filter = ["pubblicato", "categoria"]
    search_fields = ["titolo", "sommario"]
    prepopulated_fields = {"slug": ("titolo",)}
    inlines = [CommentoInline]
