from django.db import models


class Contatto(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=30, blank=True)
    citta = models.CharField("città", max_length=80, blank=True)
    creato = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome", "pk"]
        verbose_name_plural = "contatti"

    def __str__(self) -> str:
        return self.nome
