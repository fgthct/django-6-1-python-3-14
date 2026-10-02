"""Genera un CSV di contatti finti ma realistici (con errori, duplicati e domini internazionali)."""
import csv
import random
import sys

dominii = ["example.com", "bottegaetnea.example", "mail.example.org", "bücher.example", "città.example", "caffè.example"]
nomi = ["mario rossi", "  LUCIA   bianchi ", "Giuseppe Verdi", "anna maria  esposito", "Tommaso d'Aquino", "  "]

def genera(percorso, n, seme=1):
    r = random.Random(seme)
    with open(percorso, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["email", "nome"])
        for i in range(n):
            if r.random() < 0.02:
                email = f"senza-chiocciola{i}.example.com"          # non valida
            elif r.random() < 0.02:
                email = f"x{r.randrange(n // 10)}@{r.choice(dominii)}"  # duplicati probabili
            else:
                email = f"utente{i}@{r.choice(dominii)}"
            w.writerow([email, r.choices(nomi, weights=[10, 10, 10, 10, 10, 1])[0]])

if __name__ == "__main__":
    genera(sys.argv[1], int(sys.argv[2]))
