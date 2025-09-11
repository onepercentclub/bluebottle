from rest_framework.parsers import JSONParser

from bluebottle.activity_pub.processor import processor, default_context
from bluebottle.activity_pub.utils import underscore


class JSONLDParser(JSONParser):
    """
    JSON-LD parser.
    """
    media_type = 'application/ld+json'

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Simply return a string representing the body of the request.
        """
        result = super().parse(stream, media_type, parser_context)
        compacted = processor.compact(
            result,
            default_context,
            {}
        )
        del compacted['@context']

        return underscore(compacted)
