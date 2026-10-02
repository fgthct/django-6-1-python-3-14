from django.db import models
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import AttivitaForm
from .models import Attivita


class AttivitaListView(ListView):
    model = Attivita
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().fetch_mode(models.FETCH_PEERS)
        stato = self.request.GET.get("stato")
        if stato == "aperte":
            queryset = queryset.filter(completata=False)
        elif stato == "completate":
            queryset = queryset.filter(completata=True)
        return queryset

    def get_context_data(self, **kwargs):
        contesto = super().get_context_data(**kwargs)
        contesto["stato"] = self.request.GET.get("stato", "")
        return contesto


class AttivitaCreateView(CreateView):
    model = Attivita
    form_class = AttivitaForm
    success_url = reverse_lazy("todo:elenco")


class AttivitaUpdateView(UpdateView):
    model = Attivita
    form_class = AttivitaForm
    success_url = reverse_lazy("todo:elenco")


class AttivitaDeleteView(DeleteView):
    model = Attivita
    success_url = reverse_lazy("todo:elenco")


class AttivitaToggleView(View):
    """Inverte lo stato 'completata' (solo POST)."""

    http_method_names = ["post"]

    def post(self, request, pk):
        attivita = get_object_or_404(Attivita, pk=pk)
        attivita.completata = not attivita.completata
        attivita.save(update_fields=["completata"])
        return redirect("todo:elenco")
