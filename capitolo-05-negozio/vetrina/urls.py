from django.urls import path

from . import views

app_name = "vetrina"

urlpatterns = [
    path("", views.catalogo, name="catalogo"),
    path("carrello/", views.carrello, name="carrello"),
    path("carrello/aggiungi/<int:pk>/", views.aggiungi, name="aggiungi"),
    path("carrello/imposta/<int:pk>/", views.imposta, name="imposta"),
    path("ordina/", views.ordina, name="ordina"),
    path("grazie/<int:pk>/", views.grazie, name="grazie"),
]
