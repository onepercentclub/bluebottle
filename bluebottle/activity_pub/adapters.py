from urllib.parse import urlparse

import requests
from io import BytesIO

from requests_http_signature import HTTPSignatureAuth, algorithms, HTTPSignatureKeyResolver

from django.urls import resolve

from bluebottle.activity_pub.parsers import JSONLDParser
from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.activity_pub.models import Actor, Follow
from bluebottle.activity_pub.utils import is_local

from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key

from bluebottle.webfinger.client import client


class JSONLDKeyResolver(HTTPSignatureKeyResolver):
    def get_actor(self, url):
        if is_local(url):
            resolved_url = resolve(urlparse(url).path)
            return Actor.objects.get(**resolved_url.kwargs)
        else:
            from bluebottle.activity_pub.serializers import ActorSerializer
            return adapter.sync(url, ActorSerializer)

    def resolve_public_key(self, key_id):
        actor = self.get_actor(key_id)

        return load_pem_public_key(
            bytes(actor.public_key.public_key_pem, encoding='utf-8')
        )

    def resolve_private_key(self, key_id):
        actor = self.get_actor(key_id)

        return load_pem_private_key(
            bytes(actor.public_key.private_key.private_key_pem, encoding='utf-8'), password=None
        )


key_resolver = JSONLDKeyResolver()


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

    def get(self, url):
        return self.do_request("get", url)

    def post(self, url, data, auth):
        return self.do_request('post', url, data=self.renderer.render(data), auth=auth)

    def sync(self, url, serializer, force=True):
        data = self.get(url)
        serializer = serializer(data=data)
        serializer.is_valid(raise_exception=True)

        return serializer.save()

    def follow(self, url):
        from bluebottle.activity_pub.serializers import ActorSerializer

        discovered_url = client.get(url)

        actor = self.sync(discovered_url, ActorSerializer)

        return Follow.objects.create(
            object=actor
        )

    def publish(self, activity):
        from bluebottle.activity_pub.serializers import ActivitySerializer

        if activity.url:
            raise TypeError('Only local activities can be published')

        data = ActivitySerializer().to_representation(activity)
        auth = self.get_auth(activity.actor)

        for actor in activity.audience:
            self.post(actor.inbox.url, data=data, auth=auth)


adapter = JSONLDAdapter()
