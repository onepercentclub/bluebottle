import requests

from bluebottle.activity_pub.parsers import JSONLDParser
from bluebottle.activity_pub.renderers import JSONLDRenderer


class JSONLDAdapter():
    def __init__(self):
        self.parser = JSONLDParser()
        self.renderer = JSONLDRenderer()

    def execute(self, method, url, data=None):
        kwargs = {'headers': {'Content-Type': 'application/ld+json'}}
        if data:
            kwargs['data'] = data

        response = getattr(requests, method)(url, **kwargs)

        return (response.raw, response.headers['content-type'])

    def do_request(self, method, url, data=None):
        (stream, media_type) = self.execute(method, url, data)
        return self.parser.parse(stream, media_type)

    def get(self, url):
        return self.do_request('get', url)

    def post(self, url, data):
        return self.do_request('post', url, data)

    def sync(self, url, serializer, force=True):
        # First try to get the existing model, so we do not create duplicates
        try:
            return serializer.Meta.model.objects.get(url=url)
        except serializer.Meta.model.DoesNotExist:
            data = self.get(url)
            serializer = serializer(data=data)
            serializer.is_valid(raise_exception=True)

            return serializer.save()

    def publish(self, activity):
        from bluebottle.activity_pub.serializers import ActivitySerializer

        if activity.url:
            raise TypeError('Only local activities can be published')

        data = self.renderer.render(
            ActivitySerializer().to_representation(activity)
        )

        for actor in activity.audience:
            self.post(actor.inbox.url, data=data)


adapter = JSONLDAdapter()
