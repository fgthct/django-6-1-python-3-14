from django.db import models


class Contatto(models.Model):
    email = models.EmailField(unique=True)
    nome = models.CharField(max_length=100)
    attivo = models.BooleanField(default=True)

    class Meta:
        ordering = ["email"]

    def __str__(self) -> str:
        return self.email


class Campagna(models.Model):
    class Stato(models.TextChoices):
        BOZZA = "bozza", "Bozza"
        IN_INVIO = "in_invio", "In invio"
        COMPLETATA = "completata", "Completata"

    oggetto = models.CharField(max_length=200)
    corpo = models.TextField(help_text="Usa {nome} per il nome del destinatario.")
    stato = models.CharField(max_length=12, choices=Stato, default=Stato.BOZZA)
    creata = models.DateTimeField(auto_now_add=True)
    avviata_il = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-creata", "-pk"]
        verbose_name_plural = "campagne"

    def __str__(self) -> str:
        return self.oggetto


class Consegna(models.Model):
    """Un messaggio per un destinatario: la riga che racconta che cosa è successo."""

    class Stato(models.TextChoices):
        IN_ATTESA = "in_attesa", "In attesa"
        INVIATA = "inviata", "Inviata"
        FALLITA = "fallita", "Fallita"

    campagna = models.ForeignKey(Campagna, on_delete=models.CASCADE, related_name="consegne")
    contatto = models.ForeignKey(Contatto, on_delete=models.CASCADE, related_name="consegne")
    stato = models.CharField(max_length=10, choices=Stato, default=Stato.IN_ATTESA)
    tentativi = models.PositiveSmallIntegerField(default=0)
    ultimo_errore = models.TextField(blank=True)
    inviata_il = models.DateTimeField(null=True, blank=True)
    # Quando il task di invio avrebbe dovuto girare: serve a ritrovare quelli andati perduti.
    dovuta_il = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(fields=["campagna", "contatto"], name="una_consegna_per_contatto"),
        ]
        indexes = [models.Index(fields=["campagna", "stato"], name="consegna_campagna_stato")]

    def __str__(self) -> str:
        return f"{self.campagna_id} → {self.contatto_id} ({self.stato})"
