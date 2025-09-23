
import requests
from io import BytesIO

from requests_http_signature import HTTPSignatureAuth, algorithms

from bluebottle.activity_pub.parsers import JSONLDParser
from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.activity_pub.models import Follow, Activity
from bluebottle.activity_pub.utils import get_platform_actor
from bluebottle.activity_pub.authentication import key_resolver

import logging

logger = logging.getLogger(__name__)
from bluebottle.webfinger.client import client

from django.db.models.signals import post_save
from django.dispatch import receiver


class JSONLDAdapter():
    def __init__(self):
        self.parser = JSONLDParser()
        self.renderer = JSONLDRenderer()

    def get_auth(self, actor):
        auth = HTTPSignatureAuth(
            key_id=actor.pub_url,
            key_resolver=key_resolver,
            signature_algorithm=algorithms.ED25519
        )
        return auth

    def execute(self, method, url, data=None, auth=None):
        kwargs = {'headers': {'Content-Type': 'application/ld+json'}, 'auth': auth}
        if data:
            kwargs['data'] = data

        response = getattr(requests, method)(url, **kwargs)
        response.raise_for_status()
        stream = BytesIO(response.content)
        return (stream, response.headers["content-type"])

    def do_request(self, method, url, data=None, auth=None):
        (stream, media_type) = self.execute(method, url, data=data, auth=auth)
        return self.parser.parse(stream, media_type)

    def get(self, url, auth=None):
        return self.do_request("get", url, auth=auth)

    def post(self, url, data, auth):
        return self.do_request('post', url, data=self.renderer.render(data), auth=auth)

    def sync(self, url, serializer, force=True):
        try:
            return serializer.Meta.model.objects.get(url=url)
        except serializer.Meta.model.DoesNotExist:
            auth = self.get_auth(get_platform_actor())
            data = self.get(url, auth=auth)
            serializer = serializer(data=data)
            serializer.is_valid(raise_exception=True)

            return serializer.save()

    def follow(self, url):
        from bluebottle.activity_pub.serializers import ActorSerializer

        discovered_url = client.get(url)
        actor = self.sync(discovered_url, ActorSerializer)
        return Follow.objects.create(object=actor)

    def publish(self, activity):
        from bluebottle.activity_pub.serializers import ActivitySerializer

        if activity.url:
            raise TypeError('Only local activities can be published')

        data = ActivitySerializer().to_representation(activity)
        auth = self.get_auth(activity.actor)

        for actor in activity.audience:
            self.post(actor.inbox.url, data=data, auth=auth)


adapter = JSONLDAdapter()


@receiver([post_save])
def publish_activity(sender, instance, **kwargs):
    try:
        if isinstance(instance, Activity) and kwargs['created'] and instance.is_local:
            adapter.publish(instance)
    except Exception as e:
        logger.error(f"Failed to publish activity: {str(e)}")
        pass
