from pyld import jsonld, ContextResolver
from cachetools import LRUCache

from bluebottle.activity_pub.document_loaders import local_document_loader

jsonld.set_document_loader(
    local_document_loader
)

processor = jsonld.JsonLdProcessor()
default_context = [
    'https://www.w3.org/ns/activitystreams',
    'https://w3id.org/security/v1',
    'https://goodup.com/json-ld',
]
processed_context = processor.process_context(
    processor._get_initial_context({}),
    {"@context": default_context},
    {
        'contextResolver': ContextResolver(LRUCache(maxsize=1000), local_document_loader),
        'documentLoader': local_document_loader
    }
)
