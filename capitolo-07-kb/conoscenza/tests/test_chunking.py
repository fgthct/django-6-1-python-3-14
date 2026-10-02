from conoscenza.chunking import Pezzo, dividi, da_incorporare

DOC = """# Titolo del documento

Introduzione senza sezione.

## Prima

Primo paragrafo.

Secondo paragrafo.

## Seconda

Un solo paragrafo.
"""


def test_il_titolo_e_le_sezioni():
    titolo, pezzi = dividi(DOC)
    assert titolo == "Titolo del documento"
    assert [(p.sezione, p.testo) for p in pezzi] == [
        ("", "Introduzione senza sezione."),
        ("Prima", "Primo paragrafo.\n\nSecondo paragrafo."),
        ("Seconda", "Un solo paragrafo."),
    ]


def test_una_sezione_lunga_si_divide_ai_paragrafi():
    paragrafi = [f"Paragrafo {i}. " + "x" * 80 for i in range(6)]
    doc = "# T\n\n## S\n\n" + "\n\n".join(paragrafi)
    _, pezzi = dividi(doc, max_caratteri=200)
    assert len(pezzi) == 3
    assert all(p.sezione == "S" for p in pezzi)
    # nessun paragrafo è stato tagliato a metà, e niente è andato perso
    assert "\n\n".join(p.testo for p in pezzi) == "\n\n".join(paragrafi)
    assert all(len(p.testo) <= 200 for p in pezzi)


def test_un_paragrafo_piu_lungo_del_massimo_resta_intero():
    lungo = "parola " * 100
    _, pezzi = dividi(f"# T\n\n## S\n\n{lungo}", max_caratteri=50)
    assert len(pezzi) == 1
    assert pezzi[0].testo == lungo.strip()


def test_i_pezzi_sono_numerati_in_ordine_di_lettura():
    _, pezzi = dividi(DOC)
    assert [p.sezione for p in pezzi] == ["", "Prima", "Seconda"]


def test_il_da_incorporare_porta_il_contesto():
    t = da_incorporare("Ferie", Pezzo("Permessi", "Si chiedono due giorni prima."))
    assert t.startswith("Ferie — Permessi\n")
    assert t.endswith("Si chiedono due giorni prima.")
    assert da_incorporare("Ferie", Pezzo("", "x")) == "Ferie\nx"


def test_documento_vuoto():
    assert dividi("") == ("", [])
