from django.urls import path

from . import views

app_name = "articoli"

urlpatterns = [
    path("", views.ArticoloListView.as_view(), name="elenco"),
    path("articolo/<slug:slug>/", views.ArticoloDetailView.as_view(), name="dettaglio"),
    path("articolo/<slug:slug>/commenta/", views.CommentaView.as_view(), name="commenta"),
]
