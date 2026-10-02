from django import forms

from .models import Ticket


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["titolo", "richiedente", "descrizione", "priorita"]


class CommentoForm(forms.Form):
    testo = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
