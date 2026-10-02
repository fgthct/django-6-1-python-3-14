from django.contrib.postgres.search import SearchHeadline, SearchQuery, SearchRank
from django.db import models
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from .forms import CommentoForm
from .models import Articolo
from .templatetags.blog_extra import FINE, INIZIO


class ArticoloListView(ListView):
    paginate_by = 6

    def get_queryset(self):
        queryset = (
            Articolo.objects.filter(pubblicato=True)
            .fetch_mode(models.FETCH_PEERS)
        )
        categoria = self.request.GET.get("categoria")
        if categoria:
            queryset = queryset.filter(categoria__slug=categoria)
        tag = self.request.GET.get("tag")
        if tag:
            queryset = queryset.filter(tags__contains=[tag])
        q = self.request.GET.get("q", "").strip()
        if q:
            query = SearchQuery(q, config="italian", search_type="websearch")
            queryset = (
                queryset.filter(ricerca=query)
                .annotate(
                    rango=SearchRank(F("ricerca"), query),
                    estratto=SearchHeadline(
                        "testo",
                        query,
                        config="italian",
                        start_sel=INIZIO,
                        stop_sel=FINE,
                        max_words=30,
                        min_words=15,
                    ),
                )
                .order_by("-rango", "-pk")
            )
        return queryset

    def get_context_data(self, **kwargs):
        contesto = super().get_context_data(**kwargs)
        contesto["q"] = self.request.GET.get("q", "").strip()
        return contesto


class ArticoloDetailView(DetailView):
    def get_queryset(self):
        return Articolo.objects.filter(pubblicato=True)

    def get_context_data(self, **kwargs):
        contesto = super().get_context_data(**kwargs)
        contesto["form"] = CommentoForm()
        contesto["commenti"] = self.object.commenti.all()
        return contesto


class CommentaView(View):
    http_method_names = ["post"]

    def post(self, request, slug):
        articolo = get_object_or_404(Articolo, slug=slug, pubblicato=True)
        form = CommentoForm(request.POST)
        if form.is_valid():
            commento = form.save(commit=False)
            commento.articolo = articolo
            commento.save()
        return redirect(articolo)
