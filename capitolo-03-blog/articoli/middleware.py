from django.http.multipartparser import MultiPartParser, MultiPartParserError

TIPI_AMMESSI = {"image/jpeg", "image/png", "image/webp", "image/gif"}


class ParserSoloImmagini(MultiPartParser):
    """Rifiuta subito i caricamenti che non dichiarano di essere immagini."""

    def parse(self):
        post, files = super().parse()
        for _, elenco in files.lists():
            for file in elenco:
                if file.content_type not in TIPI_AMMESSI:
                    raise MultiPartParserError(
                        f"Tipo di file non ammesso: {file.content_type}"
                    )
        return post, files


class ParserSoloImmaginiMiddleware:
    """Usa il parser restrittivo per le richieste dell'area di amministrazione."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/"):
            request.multipart_parser_class = ParserSoloImmagini
        return self.get_response(request)
