from django import forms

from .models import Contatto


class ContattoForm(forms.ModelForm):
    class Meta:
        model = Contatto
        fields = ["nome", "email", "telefono", "citta"]
