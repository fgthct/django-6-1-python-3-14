from django.db import models


class Progetto(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nome"]
        verbose_name_plural = "progetti"

    def __str__(self) -> str:
        return self.nome


class Attivita(models.Model):
    progetto = models.ForeignKey(
        Progetto, on_delete=models.CASCADE, related_name="attivita"
    )
    titolo = models.CharField(max_length=200)
    descrizione = models.TextField(blank=True)
    completata = models.BooleanField(default=False)
    scadenza = models.DateField(null=True, blank=True)
    creata = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["completata", "-creata", "-pk"]
        verbose_name = "attività"
        verbose_name_plural = "attività"

    def __str__(self) -> str:
        return self.titolo
