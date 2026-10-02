from decimal import Decimal

import pytest

from vetrina.models import Categoria, Prodotto


@pytest.fixture
def catalogo(db):
    cat_a = Categoria.objects.create(nome="Dispensa")
    cat_b = Categoria.objects.create(nome="Dolci")
    prodotti = []
    for i in range(14):
        prodotti.append(Prodotto.objects.create(
            categoria=cat_a if i % 2 else cat_b, nome=f"Prodotto {i:02d}",
            prezzo=Decimal("2.50") + i, giacenza=5))
    return prodotti


@pytest.fixture
def esaurito(db):
    cat = Categoria.objects.create(nome="Rari")
    return Prodotto.objects.create(categoria=cat, nome="Raro", prezzo=Decimal("9.99"), giacenza=0)
