from pyld import jsonld
from rest_framework.renderers import JSONRenderer


class JSONLDRenderer(JSONRenderer):
    media_type = "application/ld+json"
    format = "json-ld"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""

        # Add JSON-LD context
        if isinstance(data, dict):
            data["@context"] = {
                "@vocab": "https://schema.org/",
                "type": "@type",  # Map 'type' to '@type'
                "id": "@id",  # Map 'id' to '@id'
            }

        # Convert to JSON-LD
        expanded = jsonld.expand(data)
        compacted = jsonld.compact(expanded, {"@context": "https://schema.org"})

        # Render as JSON
        return super().render(compacted, accepted_media_type, renderer_context)
