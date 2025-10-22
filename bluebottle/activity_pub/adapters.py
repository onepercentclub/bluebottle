
from celery import shared_task
import requests
from io import BytesIO

from django.forms import model_to_dict
from requests_http_signature import HTTPSignatureAuth, algorithms
from django.db import connection

from bluebottle.activity_pub.parsers import JSONLDParser
from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.activity_pub.models import Follow, Activity, Publish, Announce, Accept
from bluebottle.activity_pub.utils import get_platform_actor, is_local
from bluebottle.activity_pub.authentication import key_resolver

from bluebottle.clients.utils import LocalTenant
from bluebottle.webfinger.client import client

from django.db.models.signals import post_save
from django.dispatch import receiver

import logging

from bluebottle.activity_pub.models import Organization

logger = logging.getLogger(__name__)


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
        return (stream, response.headers.get("content-type"))

    def do_request(self, method, url, data=None, auth=None):
        if is_local(url):
            raise TypeError(f'Trying to {method} to local url: {url}')

        (stream, media_type) = self.execute(method, url, data=data, auth=auth)
        if stream and media_type:
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
    def publish_to_inbox(self, activity, inbox, tenant):
        from bluebottle.activity_pub.serializers.json_ld import ActivitySerializer
        with LocalTenant(tenant, clear_tenant=True):
            try:
                data = ActivitySerializer().to_representation(activity)
                auth = self.get_auth(activity.actor)

                self.post(inbox.iri, data=data, auth=auth)
            except Exception as e:
                logger.error(e)
                print(e)
                raise

    def publish(self, activity, audience=None):
        if not activity.is_local:
            raise TypeError('Only local activities can be published')

        if isinstance(audience, (list, tuple)):
            for actor in audience:
                if not actor.inbox.is_local:
                    self.publish_to_inbox.delay(self, activity, actor.inbox, connection.tenant)
        else:
            for actor in activity.audience:
                if not actor.inbox.is_local:
                    self.publish_to_inbox.delay(self, activity, actor.inbox, connection.tenant)

    def adopt(self, event, request):
        from bluebottle.activity_pub.serializers.federated_activities import FederatedActivitySerializer
        from bluebottle.activity_pub.serializers.json_ld import EventSerializer

        data = EventSerializer(instance=event).data
        serializer = FederatedActivitySerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        follow = Follow.objects.get(object=event.source)
        organization = Publish.objects.filter(object=event).first().actor.organization

        return serializer.save(owner=follow.default_owner, host_organization=organization)


adapter = JSONLDAdapter()


@receiver([post_save])
def publish_activity(sender, instance, **kwargs):
    try:
        if isinstance(instance, (Announce, Accept)) and kwargs['created'] and instance.is_local:
            adapter.publish(instance)
    except Exception as e:
        logger.error(f"Failed to publish activity: {str(e)}")


@receiver([post_save])
def create_organization(sender, instance, **kwargs):
    try:
        if isinstance(instance, Organization) and kwargs['created'] and not instance.organization_id:
            from bluebottle.activity_pub.serializers.federated_activities import OrganizationSerializer
            serializer = OrganizationSerializer(data=model_to_dict(instance))
            serializer.is_valid(raise_exception=True)
            organization = serializer.save()
            instance.organization = organization
            instance.save(update_fields=['organization'])

    except Exception as e:
        logger.error(f"Failed to create related organization: {str(e)}")
