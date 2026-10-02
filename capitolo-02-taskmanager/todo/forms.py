from django import forms

from .models import Attivita


class AttivitaForm(forms.ModelForm):
    class Meta:
        model = Attivita
        fields = ["progetto", "titolo", "descrizione", "scadenza"]
        widgets = {
            "scadenza": forms.DateInput(attrs={"type": "date"}),
            "descrizione": forms.Textarea(attrs={"rows": 3}),
        }
