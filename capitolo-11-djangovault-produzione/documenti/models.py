from django.conf import settings
from django.db import models
from django.db.models import Exists, OuterRef, Q
from django.db.models.functions import UUID7
from pgvector.django import HnswIndex, VectorField


class DocumentoQuerySet(models.QuerySet):
    def visibili_a(self, utente):
        """I documenti che *questo* utente può vedere: il proprio, o uno a cui ha un accesso."""
        return self.filter(
            Q(proprietario=utente) | Exists(Accesso.objects.filter(documento=OuterRef("pk"), utente=utente))
        )


class Documento(models.Model):
    class Stato(models.TextChoices):
        BOZZA = "bozza", "Bozza"
        IN_REVISIONE = "in_revisione", "In revisione"
        APPROVATO = "approvato", "Approvato"

    id = models.UUIDField(primary_key=True, db_default=UUID7(), editable=False)
    titolo = models.CharField(max_length=200)
    proprietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="documenti")
    stato = models.CharField(max_length=20, choices=Stato, default=Stato.BOZZA)
    versione_corrente = models.ForeignKey(
        "Versione", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    creato = models.DateTimeField(auto_now_add=True)

    objects = DocumentoQuerySet.as_manager()

    class Meta:
        ordering = ["-creato", "-id"]

    def __str__(self):
        return self.titolo


class Versione(models.Model):
    """Una versione è immutabile: per cambiare un documento se ne crea un'altra."""

    id = models.UUIDField(primary_key=True, db_default=UUID7(), editable=False)
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name="versioni")
    numero = models.PositiveIntegerField()
    file = models.FileField(upload_to="versioni/%Y/%m/", blank=True)
    nome_file = models.CharField(max_length=200)
    testo = models.TextField()
    hash = models.CharField(max_length=64)
    autore = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    nota = models.CharField(max_length=200, blank=True)
    creata = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-numero"]
        constraints = [models.UniqueConstraint(fields=["documento", "numero"], name="una_versione_per_numero")]

    def __str__(self):
        return f"{self.documento} v{self.numero}"


class Accesso(models.Model):
    class Livello(models.IntegerChoices):
        LETTURA = 1, "Lettura"
        MODIFICA = 2, "Modifica"

    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name="accessi")
    utente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    livello = models.IntegerField(choices=Livello, default=Livello.LETTURA)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["documento", "utente"], name="un_accesso_per_utente")]

    def __str__(self):
        return f"{self.utente} → {self.documento} ({self.get_livello_display()})"


class Revisione(models.Model):
    """Una richiesta di approvazione, per *una* versione, decisa dal proprietario."""

    class Modalita(models.TextChoices):
        IN_SEQUENZA = "sequenza", "In sequenza"
        LIBERA = "libera", "Libera (decide chi arriva prima)"

    class Stato(models.TextChoices):
        APERTA = "aperta", "Aperta"
        APPROVATA = "approvata", "Approvata"
        RIMANDATA = "rimandata", "Rimandata"
        ANNULLATA = "annullata", "Annullata"

    id = models.UUIDField(primary_key=True, db_default=UUID7(), editable=False)
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name="revisioni")
    versione = models.ForeignKey(Versione, on_delete=models.PROTECT, related_name="+")
    modalita = models.CharField(max_length=10, choices=Modalita)
    messaggio = models.TextField(blank=True)
    stato = models.CharField(max_length=10, choices=Stato, default=Stato.APERTA)
    creata = models.DateTimeField(auto_now_add=True)
    conclusa = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-creata", "-id"]
        constraints = [
            # Al massimo una revisione aperta per documento: lo garantisce il database, non il codice.
            models.UniqueConstraint(
                fields=["documento"], condition=Q(stato="aperta"), name="una_revisione_aperta_per_documento"
            )
        ]

    def __str__(self):
        return f"{self.documento}: {self.get_stato_display()}"


class Partecipante(models.Model):
    class Decisione(models.TextChoices):
        IN_ATTESA = "in_attesa", "In attesa"
        APPROVATO = "approvato", "Approvato"
        RIMANDATO = "rimandato", "Rimandato"
        SUPERATO = "superato", "Non più necessario"

    revisione = models.ForeignKey(Revisione, on_delete=models.CASCADE, related_name="partecipanti")
    utente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    ordine = models.PositiveSmallIntegerField()
    decisione = models.CharField(max_length=10, choices=Decisione, default=Decisione.IN_ATTESA)
    commento = models.TextField(blank=True)
    deciso_il = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["ordine"]
        constraints = [
            models.UniqueConstraint(fields=["revisione", "utente"], name="un_partecipante_una_volta"),
            models.UniqueConstraint(fields=["revisione", "ordine"], name="un_ordine_una_volta"),
        ]

    def __str__(self):
        return f"{self.ordine}. {self.utente}"


class Evento(models.Model):
    """Il registro delle attività: si aggiunge, non si modifica mai."""

    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name="eventi")
    utente = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    tipo = models.CharField(max_length=40)
    dettaglio = models.CharField(max_length=300, blank=True)
    creato = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creato", "-id"]

    def __str__(self):
        return f"{self.tipo} · {self.documento}"


class Chunk(models.Model):
    id = models.UUIDField(primary_key=True, db_default=UUID7(), editable=False)
    versione = models.ForeignKey(Versione, on_delete=models.CASCADE, related_name="chunk")
    posizione = models.PositiveSmallIntegerField()
    testo = models.TextField()
    embedding = VectorField(dimensions=settings.EMBEDDING_DIMENSIONI, null=True, blank=True)

    class Meta:
        ordering = ["versione", "posizione"]
        constraints = [models.UniqueConstraint(fields=["versione", "posizione"], name="chunk_posizione_unica")]
        indexes = [
            HnswIndex(
                name="chunk_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]

    def __str__(self):
        return f"{self.versione} · passaggio {self.posizione}"
