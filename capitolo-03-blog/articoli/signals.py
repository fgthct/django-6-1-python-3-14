from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Commento

commenti_eliminati: list[int] = []


@receiver(post_delete, sender=Commento)
def registra_eliminazione(sender, instance, **kwargs):
    commenti_eliminati.append(instance.pk)
