
from celery import shared_task
import requests
from io import BytesIO

from requests_http_signature import HTTPSignatureAuth, algorithms
from django.db import connection

from bluebottle.activity_pub.parsers import JSONLDParser
from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.activity_pub.models import Follow, Activity, Actor, Followers, Accept
from bluebottle.activity_pub.utils import get_platform_actor, is_local
from bluebottle.activity_pub.authentication import key_resolver

import logging

logger = logging.getLogger(__name__)
from bluebottle.clients.utils import LocalTenant
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
        if is_local(url):
            raise TypeError(f'Trying to {method} to local url: {url}')

        (stream, media_type) = self.execute(method, url, data=data, auth=auth)
        return self.parser.parse(stream, media_type)

    def get(self, url, auth=None):
        return self.do_request("get", url, auth=auth)

    def post(self, url, data, auth):
        return self.do_request('post', url, data=self.renderer.render(data), auth=auth)

    def fetch(self, url):
        auth = self.get_auth(get_platform_actor())
        return self.get(url, auth=auth)

    def follow(self, url):
        from bluebottle.activity_pub.serializers.json_ld import OrganizationSerializer

        discovered_url = client.get(url)
        data = self.fetch(discovered_url)

        serializer = OrganizationSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        actor = serializer.save()
        return Follow.objects.create(object=actor)

    @shared_task(
        autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5}
    )
    def publish_to_inbox(self, activity, tenant):
        from bluebottle.activity_pub.serializers.json_ld import ActivitySerializer

        with LocalTenant(tenant, clear_tenant=True):
            data = ActivitySerializer().to_representation(activity)
            for item in activity.audience:
                if item.is_local:
                    if isinstance(item, Followers):
                        for accept in Accept.objects.filter(actor=item.actor):
                            actor = accept.object.actor
                            auth = self.get_auth(activity.actor)
                            self.post(actor.inbox.iri, data=data, auth=auth)
                else:
                    actor = Actor.objects.get(iri=item.iri)
                    auth = self.get_auth(activity.actor)
                    self.post(actor.inbox.iri, data=data, auth=auth)

                activity.to.append(item.pub_url)
                activity.save()

    def publish(self, activity):
        if not activity.is_local:
            raise TypeError('Only local activities can be published')

        self.publish_to_inbox.delay(self, activity, connection.tenant)

    def adopt(self, event, request):
        from bluebottle.activity_pub.serializers.federated_activities import FederatedActivitySerializer
        from bluebottle.activity_pub.serializers.json_ld import EventSerializer

        data = EventSerializer(instance=event).data
        serializer = FederatedActivitySerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        follow = Follow.objects.get(object=event.source)

        return serializer.save(owner=follow.default_owner)


adapter = JSONLDAdapter()


@receiver([post_save])
def publish_activity(sender, instance, **kwargs):
    try:
        if isinstance(instance, Activity) and kwargs['created'] and instance.is_local:
            adapter.publish(instance)
    except Exception as e:
        logger.error(f"Failed to publish activity: {str(e)}")
        raise
        pass
