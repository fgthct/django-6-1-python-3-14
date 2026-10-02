from django.db import models


class Categoria(models.Model):
    nome = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ["nome"]
        verbose_name_plural = "categorie"

    def __str__(self) -> str:
        return self.nome


class Prodotto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="prodotti")
    nome = models.CharField(max_length=120)
    descrizione = models.TextField(blank=True)
    prezzo = models.DecimalField(max_digits=8, decimal_places=2)
    giacenza = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["nome", "pk"]
        verbose_name_plural = "prodotti"

    def __str__(self) -> str:
        return self.nome


class Ordine(models.Model):
    email = models.EmailField()
    creato = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creato", "-pk"]


class RigaOrdine(models.Model):
    ordine = models.ForeignKey(Ordine, on_delete=models.CASCADE, related_name="righe")
    prodotto = models.ForeignKey(Prodotto, on_delete=models.PROTECT)
    quantita = models.PositiveIntegerField()
    prezzo_unitario = models.DecimalField(max_digits=8, decimal_places=2)
