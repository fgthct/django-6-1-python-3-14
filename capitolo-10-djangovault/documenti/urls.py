from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.elenco, name="elenco"),
    path("accedi/", auth_views.LoginView.as_view(template_name="documenti/accedi.html"), name="login"),
    path("esci/", auth_views.LogoutView.as_view(), name="logout"),
    path("documenti/nuovo/", views.nuovo, name="nuovo"),
    path("documenti/<uuid:pk>/", views.dettaglio, name="dettaglio"),
    path("documenti/<uuid:pk>/versione/", views.nuova_versione, name="nuova_versione"),
    path("documenti/<uuid:pk>/revisione/", views.invia_revisione, name="invia_revisione"),
    path("documenti/<uuid:pk>/decisione/", views.decidi, name="decidi"),
    path("documenti/<uuid:pk>/annulla/", views.annulla, name="annulla"),
    path("documenti/<uuid:pk>/accesso/", views.accesso, name="accesso"),
    path("documenti/<uuid:pk>/accesso/<int:utente_id>/revoca/", views.revoca, name="revoca"),
    path("documenti/<uuid:pk>/versioni/<int:numero>/scarica/", views.scarica, name="scarica"),
    path("cerca/", views.cerca_vista, name="cerca"),
    path("chiedi/", views.chiedi, name="chiedi"),
]
