import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import mailers
from django.db import models
from django.db.models.functions import UUID7

from . import tenant


class Organizzazione(models.Model):
    """Un cliente. Non ha il filtro per tenant: è la tabella che *definisce* i tenant."""

    id = models.UUIDField(primary_key=True, db_default=UUID7(), editable=False)
    slug = models.SlugField(unique=True, help_text="Il sottodominio: acme → acme.localhost")
    nome = models.CharField(max_length=100)
    mailer = models.CharField(max_length=30, default="default")
    creata = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "organizzazioni"

    def __str__(self):
        return self.nome

    def clean(self):
        if self.mailer not in mailers:
            raise ValidationError({"mailer": f"Il mailer «{self.mailer}» non esiste in MAILERS."})


class Membro(models.Model):
    """Un utente dentro un'organizzazione, con il suo ruolo. Anche questa tabella è «globale»."""

    class Ruolo(models.IntegerChoices):
        LETTORE = 1, "Lettore"
        AGENTE = 2, "Agente"
        ADMIN = 3, "Amministratore"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membri")
    organizzazione = models.ForeignKey(Organizzazione, on_delete=models.CASCADE, related_name="membri")
    ruolo = models.IntegerField(choices=Ruolo, default=Ruolo.AGENTE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "organizzazione"], name="un_ruolo_per_organizzazione"),
        ]

    def __str__(self):
        return f"{self.user} @ {self.organizzazione.slug}"

    def puo(self, ruolo_minimo):
        return self.ruolo >= ruolo_minimo


class TenantManager(models.Manager):
    """Il manager predefinito dei modelli di tenant: *fallisce chiuso*.

    Senza un tenant attivo solleva TenantMancante invece di restituire tutto.
    """

    def get_queryset(self):
        modalita = getattr(models, settings.MODALITA_FETCH)
        return super().get_queryset().filter(organizzazione=tenant.corrente()).fetch_mode(modalita)


class ModelloDiTenant(models.Model):
    organizzazione = models.ForeignKey(Organizzazione, on_delete=models.CASCADE, editable=False)

    objects = TenantManager()
    senza_filtro = models.Manager()  # per amministrazione e comandi: da usare con coscienza

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        corrente = tenant.corrente()
        if self.organizzazione_id is None:
            self.organizzazione = corrente
        elif self.organizzazione_id != corrente.pk:
            raise PermissionError("scrittura su un tenant diverso da quello attivo")
        super().save(*args, **kwargs)


class Ticket(ModelloDiTenant):
    class Stato(models.TextChoices):
        APERTO = "aperto", "Aperto"
        IN_LAVORAZIONE = "in_lavorazione", "In lavorazione"
        CHIUSO = "chiuso", "Chiuso"

    class Priorita(models.IntegerChoices):
        BASSA = 1, "Bassa"
        NORMALE = 2, "Normale"
        ALTA = 3, "Alta"

    id = models.UUIDField(primary_key=True, db_default=UUID7(), editable=False)
    titolo = models.CharField(max_length=200)
    descrizione = models.TextField(blank=True)
    richiedente = models.EmailField()
    stato = models.CharField(max_length=20, choices=Stato, default=Stato.APERTO)
    priorita = models.IntegerField(choices=Priorita, default=Priorita.NORMALE)
    assegnato = models.ForeignKey(Membro, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    creato = models.DateTimeField(auto_now_add=True)

    class Meta:
        # L'ordinamento completo: «creato» può ripetersi, «id» no.
        ordering = ["-creato", "-id"]
        indexes = [models.Index(fields=["organizzazione", "stato", "-creato"], name="ticket_org_stato_creato")]

    def __str__(self):
        return self.titolo


class Commento(ModelloDiTenant):
    id = models.UUIDField(primary_key=True, db_default=UUID7(), editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="commenti")
    autore = models.ForeignKey(Membro, null=True, on_delete=models.SET_NULL, related_name="+")
    testo = models.TextField()
    creato = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creato", "id"]


class ChiaveApi(models.Model):
    """Una chiave per l'API. Si conserva solo l'impronta (hash): il testo si vede una volta sola."""

    membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name="chiavi")
    prefisso = models.CharField(max_length=12, unique=True)
    impronta = models.CharField(max_length=64)
    creata = models.DateTimeField(auto_now_add=True)
    revocata_il = models.DateTimeField(null=True, blank=True)


class ViolazioneCsp(models.Model):
    """Un rapporto del browser: la politica ha bloccato (o avrebbe bloccato) qualcosa."""

    host = models.CharField(max_length=255)
    direttiva = models.CharField(max_length=100)
    risorsa_bloccata = models.CharField(max_length=500, blank=True)
    documento = models.CharField(max_length=500, blank=True)
    solo_osservazione = models.BooleanField(default=False)
    ricevuta = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ricevuta", "-id"]
