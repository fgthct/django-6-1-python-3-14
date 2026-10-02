from annotationlib import Format, get_annotations


class Nodo:
    # In Python 3.14 'Nodo' non serve più tra virgolette
    def __init__(self, valore: int, successivo: Nodo | None = None):
        self.valore = valore
        self.successivo = successivo


def somma(a: int, b: Utente) -> Risultato:   # Utente e Risultato non esistono ancora
    ...


print(get_annotations(Nodo.__init__, format=Format.FORWARDREF))
print(get_annotations(somma, format=Format.STRING))


class Utente: ...
class Risultato: ...


print(get_annotations(somma))   # ora i nomi esistono: valutazione riuscita
