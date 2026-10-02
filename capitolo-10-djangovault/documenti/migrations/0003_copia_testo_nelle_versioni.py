import hashlib

from django.db import migrations
from django.utils.text import slugify


def testo_nella_prima_versione(apps, schema_editor):
    """Ogni documento del prototipo diventa un documento con una versione, la numero 1.

    Si usano i modelli *storici* (apps.get_model), non quelli di documenti.models: una
    migrazione deve funzionare con la forma che le tabelle avevano in quel momento.
    Non tocca il file system: le versioni importate non hanno un file, solo il testo.
    """
    Documento = apps.get_model("documenti", "Documento")
    Versione = apps.get_model("documenti", "Versione")
    for documento in Documento.objects.filter(versione_corrente=None).iterator():
        testo = documento.testo or ""
        versione = Versione.objects.create(
            documento=documento,
            numero=1,
            nome_file=f"{slugify(documento.titolo) or 'documento'}.txt",
            testo=testo,
            hash=hashlib.sha256(testo.encode()).hexdigest(),
            autore_id=documento.proprietario_id,
            nota="Importato dal prototipo",
        )
        documento.versione_corrente = versione
        documento.save(update_fields=["versione_corrente"])


def versione_nel_testo(apps, schema_editor):
    """La strada del ritorno: il testo della versione corrente torna nel vecchio campo."""
    Documento = apps.get_model("documenti", "Documento")
    for documento in Documento.objects.exclude(versione_corrente=None).select_related("versione_corrente"):
        documento.testo = documento.versione_corrente.testo
        documento.save(update_fields=["testo"])


class Migration(migrations.Migration):
    dependencies = [("documenti", "0002_versioni_revisioni_chunk")]
    operations = [migrations.RunPython(testo_nella_prima_versione, versione_nel_testo)]
