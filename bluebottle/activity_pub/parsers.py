from rest_framework.parsers import JSONParser
from rest_framework.exceptions import ParseError

from bluebottle.activity_pub.processor import processor, default_context
from bluebottle.activity_pub.utils import underscore


class JSONLDParser(JSONParser):
    """
    JSON-LD parser.
    """
    media_type = 'application/ld+json'

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parse JSON-LD data from the input stream.
        """
        if stream is None:
            raise ParseError('No content to parse')

        try:
            result = super().parse(stream, media_type, parser_context)
            compacted = processor.compact(
                result,
                default_context,
                {}
            )
            del compacted['@context']
            return underscore(compacted)
        except Exception as e:
            raise ParseError(f'JSON parse error - {str(e)}')
