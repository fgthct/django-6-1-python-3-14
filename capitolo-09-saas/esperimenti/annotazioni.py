"""Python 3.14: le annotazioni non vengono valutate subito. Gli schemi dell'API possono citare classi non ancora definite."""

import annotationlib

from esperimenti import prelude  # noqa: F401
from assistenza.api import TicketOut

print("campo 'assegnato' di TicketOut :", TicketOut.model_fields["assegnato"].annotation)
print("annotazioni grezze (FORWARDREF):", {k: v for k, v in annotationlib.get_annotations(TicketOut, format=annotationlib.Format.FORWARDREF).items() if k == "assegnato"})
print("TicketOut è definita prima di MembroOut nel file, eppure:", TicketOut.model_json_schema()["properties"]["assegnato"])
