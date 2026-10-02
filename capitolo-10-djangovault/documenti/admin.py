from django.contrib import admin

from .models import Documento, Evento, Revisione

admin.site.register(Documento)
admin.site.register(Revisione)
admin.site.register(Evento)
