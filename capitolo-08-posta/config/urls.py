from django.contrib import admin
from django.urls import path

from campagne import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.elenco, name="elenco"),
    path("campagne/<int:pk>/", views.dettaglio, name="dettaglio"),
    path("campagne/<int:pk>/avanzamento/", views.avanzamento, name="avanzamento"),
    path("campagne/<int:pk>/avvia/", views.avvia, name="avvia"),
]
