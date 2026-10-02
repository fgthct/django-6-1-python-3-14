from django.shortcuts import render

from . import ricerca
from .rag import rispondi

MODI = {
    "ibrida": "Ibrida",
    "significato": "Per significato",
    "parole": "Per parole",
}


def indice(request):
    return render(request, "conoscenza/indice.html", {"modi": MODI})


def cerca(request):
    domanda = request.GET.get("q", "").strip()
    modo = request.GET.get("modo", "ibrida")
    if modo not in MODI:
        modo = "ibrida"
    risultati = []
    if domanda:
        if modo == "ibrida":
            risultati = ricerca.cerca_ibrida(domanda, 5)
        elif modo == "significato":
            risultati = [
                ricerca.Risultato(c, 1 - c.distanza, i, None)
                for i, c in enumerate(ricerca.cerca_per_significato(domanda, 5), start=1)
            ]
        else:
            risultati = [
                ricerca.Risultato(c, c.rango, None, i)
                for i, c in enumerate(ricerca.cerca_per_parole(domanda, 5), start=1)
            ]
    contesto = {"domanda": domanda, "modo": modo, "risultati": risultati}
    return render(request, "conoscenza/indice.html#risultati", contesto)


def chiedi(request):
    domanda = request.GET.get("q", "").strip()
    risposta = rispondi(domanda) if domanda else None
    return render(request, "conoscenza/indice.html#risposta", {"domanda": domanda, "risposta": risposta})
