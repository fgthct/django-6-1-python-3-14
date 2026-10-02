"""Le regole del prodotto. Viste e comandi chiamano queste funzioni, e solo queste, per cambiare qualcosa."""

import hashlib
import os
from contextlib import contextmanager

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from . import permessi
from .indicizzazione import indicizza_versione
from .models import Accesso, Documento, Evento, Partecipante, Revisione, Versione
from .notifiche import invia_avviso

MAX_REVISORI = 6


class ErroreDiDominio(Exception):
    """Una richiesta valida in sé, ma non ammessa nello stato in cui è il documento."""


def _evento(utente, documento, tipo, dettaglio=""):
    Evento.objects.create(documento=documento, utente=utente, tipo=tipo, dettaglio=dettaglio[:300])


def _avvisa(utenti, oggetto, corpo):
    """Mai dentro la transazione: se facesse rollback, avviseremmo di qualcosa che non è successo."""
    ids = [u.pk for u in utenti]
    if ids:
        transaction.on_commit(lambda: invia_avviso.enqueue(utenti_ids=ids, oggetto=oggetto, corpo=corpo))


@contextmanager
def _file_da_ripulire():
    """Se qualcosa va storto, i file già scritti sul disco non devono restare orfani."""
    salvati = []
    try:
        yield salvati
    except BaseException:
        for nome in salvati:
            default_storage.delete(nome)
        raise


def _leggi(file):
    if file.size > settings.DIMENSIONE_MASSIMA_FILE:
        raise ErroreDiDominio("Il file è troppo grande.")
    contenuto = file.read()
    try:
        testo = contenuto.decode("utf-8")
    except UnicodeDecodeError:
        raise ErroreDiDominio("Per ora si accettano solo file di testo (UTF-8).") from None
    if "\x00" in testo:
        raise ErroreDiDominio("Il file non sembra un file di testo.")
    return contenuto, testo, hashlib.sha256(contenuto).hexdigest()


def _nuova_versione(documento, utente, file, nota, salvati):
    contenuto, testo, impronta = _leggi(file)
    ultima = documento.versioni.aggregate(m=Max("numero"))["m"] or 0
    nome = os.path.basename(file.name)[:200] or "documento.txt"
    versione = Versione(
        documento=documento, numero=ultima + 1, nome_file=nome, testo=testo, hash=impronta, autore=utente, nota=nota
    )
    versione.file.save(nome, ContentFile(contenuto), save=False)
    salvati.append(versione.file.name)
    versione.save()
    documento.versione_corrente = versione
    documento.save(update_fields=["versione_corrente"])
    transaction.on_commit(lambda: indicizza_versione.enqueue(versione_id=str(versione.pk)))
    return versione


def crea_documento(utente, titolo, file, nota=""):
    with _file_da_ripulire() as salvati, transaction.atomic():
        documento = Documento.objects.create(titolo=titolo, proprietario=utente)
        _nuova_versione(documento, utente, file, nota, salvati)
        _evento(utente, documento, "creato", titolo)
    return documento


def carica_versione(utente, documento, file, nota=""):
    with _file_da_ripulire() as salvati, transaction.atomic():
        # Il lucchetto sulla riga del documento: due caricamenti insieme non prendono lo stesso numero.
        documento = Documento.objects.select_for_update().get(pk=documento.pk)
        permessi.richiedi(utente, documento, permessi.MODIFICA)
        if documento.stato == Documento.Stato.IN_REVISIONE:
            raise ErroreDiDominio(
                "Il documento è in revisione: annulla la revisione prima di caricare una nuova versione."
            )
        corrente = documento.versione_corrente
        if corrente is not None and _leggi(file)[2] == corrente.hash:
            raise ErroreDiDominio("Il file è identico alla versione corrente.")
        file.seek(0)
        versione = _nuova_versione(documento, utente, file, nota, salvati)
        if documento.stato == Documento.Stato.APPROVATO:
            documento.stato = Documento.Stato.BOZZA  # una versione nuova va approvata di nuovo
            documento.save(update_fields=["stato"])
        _evento(utente, documento, "nuova_versione", f"v{versione.numero}: {nota}")
    return versione


@transaction.atomic
def concedi_accesso(utente, documento, destinatario, livello):
    permessi.richiedi(utente, documento, permessi.PROPRIETARIO)
    if destinatario.pk == documento.proprietario_id:
        raise ErroreDiDominio("Il proprietario ha già tutti i permessi.")
    Accesso.objects.update_or_create(documento=documento, utente=destinatario, defaults={"livello": livello})
    _evento(utente, documento, "accesso", f"{destinatario} → {Accesso.Livello(livello).label}")


@transaction.atomic
def revoca_accesso(utente, documento, destinatario):
    permessi.richiedi(utente, documento, permessi.PROPRIETARIO)
    if Partecipante.objects.filter(
        revisione__documento=documento, revisione__stato=Revisione.Stato.APERTA, utente=destinatario
    ).exists():
        raise ErroreDiDominio("L'utente è un revisore di una revisione aperta.")
    Accesso.objects.filter(documento=documento, utente=destinatario).delete()
    _evento(utente, documento, "accesso_revocato", str(destinatario))


@transaction.atomic
def invia_in_revisione(utente, documento, revisori, modalita, messaggio=""):
    """Solo il proprietario sceglie i revisori, e solo lui."""
    documento = Documento.objects.select_for_update().get(pk=documento.pk)
    permessi.richiedi(utente, documento, permessi.PROPRIETARIO)
    if documento.stato != Documento.Stato.BOZZA:
        raise ErroreDiDominio("Si può inviare in revisione solo una bozza.")
    ids = [r.pk for r in revisori]
    if not ids:
        raise ErroreDiDominio("Scegli almeno un revisore.")
    if len(set(ids)) != len(ids):
        raise ErroreDiDominio("Un revisore compare due volte.")
    if documento.proprietario_id in ids:
        raise ErroreDiDominio("Non puoi essere revisore dei tuoi documenti.")
    if len(ids) > MAX_REVISORI:
        raise ErroreDiDominio(f"Al massimo {MAX_REVISORI} revisori.")
    revisione = Revisione.objects.create(
        documento=documento, versione=documento.versione_corrente, modalita=modalita, messaggio=messaggio
    )
    for ordine, revisore in enumerate(revisori, start=1):
        Partecipante.objects.create(revisione=revisione, utente=revisore, ordine=ordine)
        Accesso.objects.get_or_create(documento=documento, utente=revisore)  # chi deve leggere, può leggere
    documento.stato = Documento.Stato.IN_REVISIONE
    documento.save(update_fields=["stato"])
    _evento(
        utente,
        documento,
        "inviato_in_revisione",
        f"{revisione.get_modalita_display()}: " + ", ".join(map(str, revisori)),
    )
    da_avvisare = revisori[:1] if modalita == Revisione.Modalita.IN_SEQUENZA else revisori
    _avvisa(
        da_avvisare,
        f"Revisione richiesta: {documento.titolo}",
        f"{utente} ti chiede di rivedere «{documento.titolo}» "
        f"(versione {documento.versione_corrente.numero}).\n\n{messaggio}",
    )
    return revisione


def _concludi(revisione, stato):
    revisione.stato = stato
    revisione.conclusa = timezone.now()
    revisione.save(update_fields=["stato", "conclusa"])
    revisione.partecipanti.filter(decisione=Partecipante.Decisione.IN_ATTESA).update(
        decisione=Partecipante.Decisione.SUPERATO
    )


@transaction.atomic
def decidi(utente, documento, approva, commento=""):
    # Lo stesso lucchetto di «invia» e «carica»: due revisori che premono insieme vengono messi in fila.
    documento = Documento.objects.select_for_update().get(pk=documento.pk)
    revisione = documento.revisioni.filter(stato=Revisione.Stato.APERTA).first()
    if revisione is None:
        raise ErroreDiDominio("Non c'è una revisione aperta (forse è già stata conclusa).")
    mio = revisione.partecipanti.filter(utente=utente).first()
    if mio is None:
        raise PermissionDenied("Non sei un revisore di questo documento.")
    if mio.decisione != Partecipante.Decisione.IN_ATTESA:
        raise ErroreDiDominio("Hai già deciso.")
    if revisione.modalita == Revisione.Modalita.IN_SEQUENZA:
        prossimo = revisione.partecipanti.filter(decisione=Partecipante.Decisione.IN_ATTESA).first()
        if prossimo.pk != mio.pk:
            raise ErroreDiDominio("Non è ancora il tuo turno.")
    if not approva and not commento.strip():
        raise ErroreDiDominio("Per rimandare indietro un documento serve un commento.")

    mio.decisione = Partecipante.Decisione.APPROVATO if approva else Partecipante.Decisione.RIMANDATO
    mio.commento = commento
    mio.deciso_il = timezone.now()
    mio.save()
    proprietario = documento.proprietario
    if not approva:
        _concludi(revisione, Revisione.Stato.RIMANDATA)
        documento.stato = Documento.Stato.BOZZA
        documento.save(update_fields=["stato"])
        _evento(utente, documento, "rimandato", commento)
        _avvisa(
            [proprietario],
            f"Rimandato in bozza: {documento.titolo}",
            f"{utente} ha rimandato il documento.\n\n{commento}",
        )
        return revisione
    _evento(utente, documento, "approvato", commento)
    ancora = revisione.partecipanti.filter(decisione=Partecipante.Decisione.IN_ATTESA)
    if revisione.modalita == Revisione.Modalita.LIBERA or not ancora.exists():
        _concludi(revisione, Revisione.Stato.APPROVATA)
        documento.stato = Documento.Stato.APPROVATO
        documento.save(update_fields=["stato"])
        _avvisa([proprietario], f"Approvato: {documento.titolo}", f"{utente} ha approvato il documento.")
    else:
        prossimo = ancora.first().utente
        _avvisa(
            [prossimo],
            f"Tocca a te: {documento.titolo}",
            f"{utente} ha approvato. Ora è il tuo turno.\n\n{revisione.messaggio}",
        )
    return revisione


@transaction.atomic
def annulla_revisione(utente, documento):
    documento = Documento.objects.select_for_update().get(pk=documento.pk)
    permessi.richiedi(utente, documento, permessi.PROPRIETARIO)
    revisione = documento.revisioni.filter(stato=Revisione.Stato.APERTA).first()
    if revisione is None:
        raise ErroreDiDominio("Non c'è una revisione aperta.")
    _concludi(revisione, Revisione.Stato.ANNULLATA)
    documento.stato = Documento.Stato.BOZZA
    documento.save(update_fields=["stato"])
    _evento(utente, documento, "revisione_annullata")
