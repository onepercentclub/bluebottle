from rest_framework import renderers

from bluebottle.activity_pub.processor import default_context, processor
from bluebottle.activity_pub.utils import camelize


class JSONLDRenderer(renderers.JSONRenderer):
    media_type = 'application/ld+json'
    format = 'application/ld+json'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        camelized = camelize(data, False)
        camelized['@context'] = default_context
        compacted = processor.compact(camelized, default_context, {})

        return super().render(compacted, accepted_media_type, renderer_context)
