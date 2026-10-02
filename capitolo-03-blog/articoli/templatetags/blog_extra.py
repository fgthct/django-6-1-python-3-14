from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

INIZIO = "⟦"
FINE = "⟧"


@register.filter
def evidenzia(testo):
    """Converte i segnaposto di SearchHeadline in <mark>, dopo aver fatto l'escape."""
    sicuro = escape(testo).replace(INIZIO, "<mark>").replace(FINE, "</mark>")
    return mark_safe(sicuro)
