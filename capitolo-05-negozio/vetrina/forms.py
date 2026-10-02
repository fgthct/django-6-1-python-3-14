from django import forms


class QuantitaForm(forms.Form):
    quantita = forms.IntegerField(min_value=0, max_value=99)


class OrdineForm(forms.Form):
    email = forms.EmailField()
