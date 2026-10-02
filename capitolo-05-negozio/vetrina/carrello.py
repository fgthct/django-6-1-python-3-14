from decimal import Decimal

from .models import Prodotto

CHIAVE = "carrello"


class Carrello:
    """Il carrello vive nella sessione come {pk: quantità}. I prezzi no: si leggono dal database."""

    def __init__(self, dati: dict[str, int]):
        self.dati = dati

    @classmethod
    def da_sessione(cls, sessione):
        return cls(sessione.get(CHIAVE, {}))

    @classmethod
    async def da_sessione_async(cls, sessione):
        return cls(await sessione.aget(CHIAVE, {}))

    def salva(self, sessione):
        sessione[CHIAVE] = self.dati
        sessione.modified = True

    def imposta(self, pk: int, quantita: int):
        if quantita > 0:
            self.dati[str(pk)] = quantita
        else:
            self.dati.pop(str(pk), None)

    def quantita(self, pk: int) -> int:
        return self.dati.get(str(pk), 0)

    def conteggio(self) -> int:
        return sum(self.dati.values())

    def righe(self):
        prodotti = Prodotto.objects.in_bulk(int(pk) for pk in self.dati)
        righe = []
        for pk, quantita in self.dati.items():
            prodotto = prodotti.get(int(pk))
            if prodotto is not None:
                righe.append({"prodotto": prodotto, "quantita": quantita,
                              "subtotale": prodotto.prezzo * quantita})
        righe.sort(key=lambda r: (r["prodotto"].nome, r["prodotto"].pk))
        return righe

    def totale(self, righe=None) -> Decimal:
        return sum((r["subtotale"] for r in (righe if righe is not None else self.righe())), Decimal("0"))
