# Django 6.1 con Python 3.14 — il codice del libro

Codice degli esempi e dei progetti del libro **«Django 6.1 con Python 3.14»**
di Franky Bonanno (*Dal primo progetto alla produzione: applicazioni web complete
con PostgreSQL, ricerca semantica con pgvector e interfacce dinamiche con HTMX*),
disponibile su Amazon.

📘 **Il libro:** [Django 6.1 con Python 3.14 su Amazon](https://amzn.eu/d/0drsqpB8)  
Gli altri miei titoli: [pagina autore Amazon](https://www.amazon.it/Franky-Bonanno/e/B0GCXTHBK3).

Ogni cartella è un progetto **autonomo**: puoi entrare, installare le dipendenze
e avviarlo senza toccare il resto. Puoi anche fare il fork di un solo progetto
e usarlo come base per il tuo.

## Cartelle

| Cartella | Contenuto |
|---|---|
| `capitolo-01-python-3-14` | Piccoli script sulle novità di Python 3.14 |
| `capitolo-02-taskmanager` | Primo progetto: task manager |
| `capitolo-03-blog` | Blog con PostgreSQL e ricerca full-text |
| `capitolo-04-rubrica` | Rubrica di contatti |
| `capitolo-05-negozio` | Negozio con vetrina, carrello e ordini (HTMX) |
| `capitolo-06-semantica` | Frasi e ricerca per significato con pgvector |
| `capitolo-07-kb` | Knowledge base con ricerca semantica |
| `capitolo-08-posta` | Campagne email in background (`django.tasks`, Redis) |
| `capitolo-09-saas` | Helpdesk multi-tenant con API e dashboard |
| `capitolo-10-djangovault` | DjangoVault: gestione documentale (versione del capitolo 10) |
| `capitolo-11-djangovault-produzione` | DjangoVault con test, Docker e CI |
| `appendice-a-lab` | Laboratorio per l'aggiornamento da Django 5.2 a 6.x |

## Requisiti

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL (con l'estensione pgvector dal capitolo 6 in poi)

Ogni progetto ha un `pyproject.toml` e un `uv.lock`; dove serve, un `README.md`
con le istruzioni specifiche. Nel dubbio:

```bash
cd capitolo-02-taskmanager
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

## Segnalazioni

Hai trovato un errore o qualcosa che non funziona con la tua versione?
Apri una *issue*: indica la cartella, la versione di Python/Django/PostgreSQL
e il messaggio d'errore completo.

## Licenza

Codice rilasciato con licenza MIT (vedi `LICENSE`). Il testo del libro non è
incluso e resta protetto dal diritto d'autore.
