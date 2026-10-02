def mostra(descrizione, queryset):
    print(f"{descrizione:<40} {queryset.totally_ordered}")


mostra("predefinito (Meta.ordering)", Attivita.objects.all())
mostra("order_by('completata')", Attivita.objects.order_by("completata"))
mostra(
    "order_by('completata', '-creata')",
    Attivita.objects.order_by("completata", "-creata"),
)
mostra(
    "order_by('completata', '-creata', 'pk')",
    Attivita.objects.order_by("completata", "-creata", "pk"),
)
mostra("order_by()  (nessun ordinamento)", Attivita.objects.order_by())
