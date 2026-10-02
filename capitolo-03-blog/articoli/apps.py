from django.apps import AppConfig


class ArticoliConfig(AppConfig):
    name = "articoli"

    def ready(self):
        from . import signals  # noqa: F401
