from html import escape
from string.templatelib import Interpolation, Template


def html(template: Template) -> str:
    """Renderizza un t-string come HTML, facendo l'escape delle interpolazioni."""
    risultato = []
    for parte in template:
        if isinstance(parte, Interpolation):
            risultato.append(escape(str(parte.value)))
        else:
            risultato.append(parte)
    return "".join(risultato)


commento = "<script>alert('XSS')</script>"
print(html(t"<p>{commento}</p>"))
# <p>&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;</p>
