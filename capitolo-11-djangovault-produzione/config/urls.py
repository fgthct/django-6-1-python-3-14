from django.contrib import admin
from django.urls import include, path

from . import salute

urlpatterns = [
    path("salute/", salute.salute, name="salute"),
    path("pronto/", salute.pronto, name="pronto"),
    path("admin/", admin.site.urls),
    path("", include("documenti.urls")),
]
