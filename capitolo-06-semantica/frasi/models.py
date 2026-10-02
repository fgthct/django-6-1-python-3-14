from django.conf import settings
from django.db import models
from pgvector.django import HnswIndex, VectorField


class Frase(models.Model):
    testo = models.CharField(max_length=300, unique=True)
    argomento = models.CharField(max_length=40)
    embedding = VectorField(dimensions=settings.EMBEDDING_DIMENSIONI, null=True, blank=True)

    class Meta:
        ordering = ["argomento", "pk"]

    def __str__(self) -> str:
        return self.testo


class PuntoProva(models.Model):
    """Solo per il laboratorio sugli indici: vettori sintetici, non testi veri."""

    gruppo = models.PositiveSmallIntegerField()
    embedding = VectorField(dimensions=settings.EMBEDDING_DIMENSIONI)

    class Meta:
        indexes = [
            HnswIndex(
                name="puntoprova_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]
