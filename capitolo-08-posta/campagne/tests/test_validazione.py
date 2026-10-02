import pytest

from campagne.validazione import valida_blocco


def una(email, nome="Mario Rossi"):
    return valida_blocco([(email, nome)])[0]


def test_normalizza_maiuscole_e_spazi():
    assert una("  Mario.Rossi@EXAMPLE.com ", "  mario   ROSSI ") == ("mario.rossi@example.com", "Mario Rossi", None)


def test_i_domini_internazionali_diventano_punycode():
    email, _, errore = una("info@bücher.example")
    assert errore is None and email == "info@xn--bcher-kva.example"


def test_i_caratteri_a_larghezza_piena_si_normalizzano():
    # NFKC: «ｍａｒｉｏ＠ｅｘａｍｐｌｅ．ｃｏｍ» è lo stesso indirizzo scritto con altri caratteri
    assert una("ｍａｒｉｏ＠ｅｘａｍｐｌｅ．ｃｏｍ")[0] == "mario@example.com"


@pytest.mark.parametrize("email", ["senza-chiocciola.example.com", "a@b", "a b@example.com", "@example.com", "a@@example.com", ""])
def test_gli_indirizzi_non_validi_sono_scartati(email):
    risultato = una(email)
    assert risultato[0] is None and risultato[2] is not None


def test_il_nome_e_obbligatorio():
    assert una("a@example.com", "   ") == (None, "", "nome mancante")


def test_un_dominio_impossibile_non_fa_crollare_il_blocco():
    esiti = valida_blocco([("a@" + "x" * 300 + ".example", "A"), ("b@example.com", "B")])
    assert esiti[0][2] == "dominio non valido"
    assert esiti[1][0] == "b@example.com"


def test_l_ordine_e_la_lunghezza_si_conservano():
    righe = [(f"u{i}@example.com", "N") for i in range(50)]
    assert [e[0] for e in valida_blocco(righe)] == [r[0] for r in righe]
