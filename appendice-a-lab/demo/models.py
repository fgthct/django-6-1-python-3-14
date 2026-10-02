from django.db import models


class Nota(models.Model):
    titolo = models.CharField(max_length=50)
    dati = models.JSONField(null=True)
