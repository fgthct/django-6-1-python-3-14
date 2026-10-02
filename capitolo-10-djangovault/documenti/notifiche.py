from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.tasks import task


@task
def invia_avviso(utenti_ids, oggetto, corpo):
    """Un messaggio a ciascun destinatario, separato: nessuno vede chi altro lo ha ricevuto."""
    inviati = 0
    for utente in get_user_model().objects.filter(pk__in=utenti_ids).exclude(email=""):
        EmailMessage(subject=oggetto, body=corpo, from_email=settings.EMAIL_DA, to=[utente.email]).send()
        inviati += 1
    return inviati
