from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.db.models.functions import UUID7
from pgvector.django import HnswIndex, VectorField


class Documento(models.Model):
    # L'id lo genera PostgreSQL (UUIDv7: ordinabile nel tempo, indice compatto).
    id = models.UUIDField(primary_key=True, db_default=UUID7(), editable=False)
    percorso = models.CharField(max_length=200, unique=True)
    titolo = models.CharField(max_length=200)
    # Hash del contenuto: ci dice se un documento è cambiato dall'ultima importazione.
    hash = models.CharField(max_length=64)
    importato_il = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["titolo"]

    def __str__(self) -> str:
        return self.titolo


class Chunk(models.Model):
    id = models.UUIDField(primary_key=True, db_default=UUID7(), editable=False)
    documento = models.ForeignKey(
        Documento, on_delete=models.DB_CASCADE, related_name="chunk"
    )
    posizione = models.PositiveSmallIntegerField()
    sezione = models.CharField(max_length=200, blank=True)
    testo = models.TextField()

    # Colonna calcolata dal database: non la scriviamo mai, non può andare fuori sincrono.
    ricerca = models.GeneratedField(
        expression=(
            SearchVector("sezione", weight="B", config="italian")
            + SearchVector("testo", weight="A", config="italian")
        ),
        output_field=SearchVectorField(),
        db_persist=True,
    )

    embedding = VectorField(dimensions=settings.EMBEDDING_DIMENSIONI, null=True, blank=True)
    # Quale modello ha prodotto il vettore: serve a sapere cosa rigenerare quando cambia.
    modello = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["documento", "posizione"]
        constraints = [
            models.UniqueConstraint(
                fields=["documento", "posizione"], name="chunk_posizione_unica"
            )
        ]
        indexes = [
            GinIndex(fields=["ricerca"], name="chunk_ricerca_gin"),
            HnswIndex(
                name="chunk_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]

    def __str__(self) -> str:
        return f"{self.documento} · {self.sezione or '(intro)'} #{self.posizione}"
