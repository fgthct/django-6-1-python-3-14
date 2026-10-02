from django.contrib import admin
from django.urls import path

from conoscenza import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.indice, name="indice"),
    path("cerca/", views.cerca, name="cerca"),
    path("chiedi/", views.chiedi, name="chiedi"),
]
