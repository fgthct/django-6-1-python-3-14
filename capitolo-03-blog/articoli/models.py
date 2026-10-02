from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.urls import reverse


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["nome"]
        verbose_name_plural = "categorie"

    def __str__(self) -> str:
        return self.nome


class Articolo(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.DB_SET_NULL,
        null=True,
        blank=True,
        related_name="articoli",
    )
    titolo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    sommario = models.CharField(max_length=300, blank=True)
    testo = models.TextField()
    tags = ArrayField(models.CharField(max_length=30), default=list, blank=True)
    copertina = models.ImageField(upload_to="copertine/", blank=True)
    metadati = models.JSONField(null=True, blank=True)
    pubblicato = models.BooleanField(default=False)
    pubblicato_il = models.DateTimeField(null=True, blank=True)
    creato = models.DateTimeField(auto_now_add=True)

    ricerca = models.GeneratedField(
        expression=(
            SearchVector("titolo", weight="A", config="italian")
            + SearchVector("sommario", weight="B", config="italian")
            + SearchVector("testo", weight="C", config="italian")
        ),
        output_field=SearchVectorField(),
        db_persist=True,
    )

    class Meta:
        ordering = ["-pubblicato_il", "-pk"]
        verbose_name = "articolo"
        verbose_name_plural = "articoli"
        indexes = [
            GinIndex(fields=["ricerca"]),
            GinIndex(fields=["tags"]),
        ]

    def __str__(self) -> str:
        return self.titolo

    def get_absolute_url(self) -> str:
        return reverse("articoli:dettaglio", kwargs={"slug": self.slug})


class Commento(models.Model):
    articolo = models.ForeignKey(
        Articolo, on_delete=models.DB_CASCADE, related_name="commenti"
    )
    autore = models.CharField(max_length=80)
    testo = models.TextField()
    creato = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creato", "pk"]
        verbose_name = "commento"
        verbose_name_plural = "commenti"

    def __str__(self) -> str:
        return f"{self.autore}: {self.testo[:30]}"
