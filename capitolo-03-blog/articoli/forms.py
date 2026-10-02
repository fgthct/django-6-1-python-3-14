from django import forms

from .models import Commento


class CommentoForm(forms.ModelForm):
    class Meta:
        model = Commento
        fields = ["autore", "testo"]
        widgets = {"testo": forms.Textarea(attrs={"rows": 4})}
