from django.contrib.auth import views as auth_views
from django.urls import path

from . import csp, views

urlpatterns = [
    path("", views.home, name="home"),
    path("accedi/", auth_views.LoginView.as_view(template_name="assistenza/accedi.html"), name="login"),
    path("esci/", auth_views.LogoutView.as_view(), name="logout"),
    path("csp-report/", csp.rapporto, name="csp_report"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/contatori/", views.contatori, name="contatori"),
    path("ticket/nuovo/", views.nuovo, name="nuovo"),
    path("ticket/<uuid:pk>/", views.ticket, name="ticket"),
    path("ticket/<uuid:pk>/stato/", views.cambia_stato, name="cambia_stato"),
    path("ticket/<uuid:pk>/commenti/", views.commenta, name="commenta"),
]
