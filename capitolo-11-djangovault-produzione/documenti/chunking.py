def spezza(testo: str, massimo: int = 800) -> list[str]:
    """Divide il testo in passaggi: parte dai paragrafi e li unisce finché non superano `massimo`."""
    passaggi, corrente = [], ""
    for paragrafo in (p.strip() for p in testo.split("\n\n")):
        if not paragrafo:
            continue
        while len(paragrafo) > massimo:  # un paragrafo enorme si taglia, all'ultimo spazio utile
            taglio = paragrafo.rfind(" ", 0, massimo)
            taglio = taglio if taglio > 0 else massimo
            if corrente:
                passaggi.append(corrente)
                corrente = ""
            passaggi.append(paragrafo[:taglio].strip())
            paragrafo = paragrafo[taglio:].strip()
        if corrente and len(corrente) + len(paragrafo) + 2 > massimo:
            passaggi.append(corrente)
            corrente = ""
        corrente = f"{corrente}\n\n{paragrafo}".strip()
    if corrente:
        passaggi.append(corrente)
    return passaggi
