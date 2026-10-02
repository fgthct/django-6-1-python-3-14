from django import forms
from django.contrib.auth import get_user_model

from .models import Accesso, Revisione

User = get_user_model()
NUMERO_REVISORI = 4


class UtenteChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, utente):
        return utente.get_full_name() or utente.get_username()


class NuovoDocumentoForm(forms.Form):
    titolo = forms.CharField(max_length=200)
    file = forms.FileField()
    nota = forms.CharField(max_length=200, required=False)


class NuovaVersioneForm(forms.Form):
    file = forms.FileField()
    nota = forms.CharField(max_length=200, required=False)


class RevisioneForm(forms.Form):
    """Il proprietario sceglie i revisori da elenchi a discesa: l'ordine dei campi è l'ordine dei turni."""

    modalita = forms.ChoiceField(choices=Revisione.Modalita.choices, widget=forms.RadioSelect,
                                 initial=Revisione.Modalita.IN_SEQUENZA)
    messaggio = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False,
                                help_text="Un messaggio per i revisori: che cosa guardare, che cosa ti serve.")

    def __init__(self, *args, proprietario, **kwargs):
        super().__init__(*args, **kwargs)
        scelta = User.objects.filter(is_active=True).exclude(pk=proprietario.pk).order_by("first_name", "username")
        for n in range(1, NUMERO_REVISORI + 1):
            self.fields[f"revisore_{n}"] = UtenteChoiceField(
                queryset=scelta, required=(n == 1), label=f"Revisore {n}", empty_label="—"
            )
        self.order_fields([f"revisore_{n}" for n in range(1, NUMERO_REVISORI + 1)] + ["modalita", "messaggio"])

    def revisori(self):
        scelti = [self.cleaned_data.get(f"revisore_{n}") for n in range(1, NUMERO_REVISORI + 1)]
        return [u for u in scelti if u is not None]


class DecisioneForm(forms.Form):
    commento = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False)


class AccessoForm(forms.Form):
    utente = UtenteChoiceField(queryset=User.objects.none(), label="Utente")
    livello = forms.TypedChoiceField(choices=Accesso.Livello.choices, coerce=int)

    def __init__(self, *args, proprietario, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["utente"].queryset = User.objects.filter(is_active=True).exclude(pk=proprietario.pk).order_by("username")


class DomandaForm(forms.Form):
    q = forms.CharField(max_length=300)
