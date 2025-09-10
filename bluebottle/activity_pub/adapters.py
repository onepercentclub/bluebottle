import json
import requests
from pyld import jsonld, ContextResolver
from cachetools import LRUCache

from bluebottle.activity_pub.document_loaders import local_document_loader


class JSONLDAdapter():
    def do_request(self, method, url, data=None):
        kwargs = {'headers': {'Content-Type': 'application/json'}}
        if data:
            kwargs['data'] = json.dumps(data)

        return getattr(requests, method)(url, **kwargs).json()

    def get(self, url):
        return self.do_request('get', url)

    def post(self, url, data):
        return self.do_request('post', url, data)

    def sync(self, url, serializer):
        data = self.get(url)

        serializer = serializer(data=data)
        serializer.is_valid()

        return serializer.save()

    def publish(self, activity):
        from bluebottle.activity_pub.serializers import ActivitySerializer

        data = ActivitySerializer().to_representation(activity)

        for actor in activity.audience:
            self.post(actor.inbox.url, data=data)


adapter = JSONLDAdapter()

jsonld.set_document_loader(
    local_document_loader
)

processor = jsonld.JsonLdProcessor()
default_context = ['https://www.w3.org/ns/activitystreams', 'https://w3id.org/security/v1']
processed_context = processor.process_context(
    processor._get_initial_context({}),
    {"@context": default_context},
    {
        'contextResolver': ContextResolver(LRUCache(maxsize=1000), local_document_loader),
        'documentLoader': local_document_loader
    }
)
