from django.urls import path

from . import views

app_name = "contatti"

urlpatterns = [
    path("", views.elenco, name="elenco"),
    path("conteggio/", views.conteggio, name="conteggio"),
    path("nuovo/", views.nuovo, name="nuovo"),
    path("<int:pk>/", views.dettaglio, name="dettaglio"),
    path("<int:pk>/riga/", views.riga, name="riga"),
    path("<int:pk>/modifica/", views.modifica, name="modifica"),
    path("<int:pk>/elimina/", views.elimina, name="elimina"),
]
