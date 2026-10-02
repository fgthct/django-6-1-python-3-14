from django.urls import path

from . import views

app_name = "todo"

urlpatterns = [
    path("", views.AttivitaListView.as_view(), name="elenco"),
    path("nuova/", views.AttivitaCreateView.as_view(), name="nuova"),
    path("<int:pk>/modifica/", views.AttivitaUpdateView.as_view(), name="modifica"),
    path("<int:pk>/elimina/", views.AttivitaDeleteView.as_view(), name="elimina"),
    path("<int:pk>/completa/", views.AttivitaToggleView.as_view(), name="completa"),
]
