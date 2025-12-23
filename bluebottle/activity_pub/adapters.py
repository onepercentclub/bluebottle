import logging
from io import BytesIO

import requests
from bluebottle.activity_links.models import LinkedActivity
from celery import shared_task
from django.db import connection
from django.db.models.signals import post_save
from django.dispatch import receiver
from requests_http_signature import HTTPSignatureAuth, algorithms

from bluebottle.activity_links.serializers import LinkedDeedSerializer
from bluebottle.activity_pub.authentication import key_resolver
from bluebottle.activity_pub.models import Follow, Activity, Publish, Event, Update
from bluebottle.activity_pub.models import Organization
from bluebottle.activity_pub.models import Recipient
from bluebottle.activity_pub.parsers import JSONLDParser
from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.activity_pub.utils import get_platform_actor, is_local
from bluebottle.clients.utils import LocalTenant
from bluebottle.webfinger.client import client

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
        rendered_data = self.renderer.render(data)
        return self.do_request('post', url, data=rendered_data, auth=auth)

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

    def publish(self, activity):
        if not activity.is_local:
            raise TypeError('Only local activities can be published')

        # Ensure the activity is saved so recipient relations can be accessed
        if not activity.pk:
            activity.save()

        for recipient in activity.recipients.all():
            if recipient.send:
                pass
            actor = recipient.actor
            inbox = getattr(actor, "inbox", None)
            if inbox is None or inbox.is_local:
                logger.warning(f"Actor {actor} has no inbox, skipping publish")
                continue
            publish_to_recipient.delay(activity, recipient, connection.tenant)

    def adopt(self, event, request):
        from bluebottle.activity_pub.serializers.federated_activities import FederatedActivitySerializer
        from bluebottle.activity_pub.serializers.json_ld import EventSerializer

        data = EventSerializer(instance=event).data
        serializer = FederatedActivitySerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        follow = Follow.objects.get(object=event.source)
        organization = Publish.objects.filter(object=event).first().actor.organization

        return serializer.save(owner=follow.default_owner, host_organization=organization)

    def create_event(self, activity):
        from bluebottle.activities.models import Activity as BluebottleActivity
        from bluebottle.activity_pub.serializers.federated_activities import FederatedActivitySerializer
        from bluebottle.activity_pub.serializers.json_ld import EventSerializer

        if not isinstance(activity, BluebottleActivity):
            raise TypeError('Activity must be a BluebottleActivity')

        try:
            instance = activity.event
        except Event.DoesNotExist:
            instance = None

        federated_serializer = FederatedActivitySerializer(activity)

        serializer = EventSerializer(
            data=federated_serializer.data, instance=instance
        )
        serializer.is_valid(raise_exception=True)
        event = serializer.save(activity=activity)

        if not event.publish_set.exists():
            Publish.objects.create(actor=get_platform_actor(), object=event)
        return event

    def link(self, event, instance=None, request=None):
        from bluebottle.activity_pub.serializers.json_ld import EventSerializer

        data = EventSerializer(instance=event).data
        serializer = LinkedDeedSerializer(data=data, context={'request': request}, instance=instance)
        serializer.is_valid(raise_exception=True)

        organization = Publish.objects.filter(object=event).first().actor.organization

        return serializer.save(
            event=event, host_organization=organization, status='open'
        )


adapter = JSONLDAdapter()


@shared_task(
    autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5},
    name="bluebottle.activity_pub.adapters.publish_to_recipient"
)
def publish_to_recipient(activity, recipient, tenant):
    from bluebottle.activity_pub.serializers.json_ld import ActivitySerializer

    with LocalTenant(tenant, clear_tenant=True):
        actor = recipient.actor
        inbox = getattr(actor, "inbox", None)
        if recipient.send:
            pass
        actor = recipient.actor
        if inbox is None or inbox.is_local:
            logger.warning(f"Actor {actor} has no inbox, skipping publish")
            pass
        try:
            data = ActivitySerializer().to_representation(activity)
            auth = adapter.get_auth(activity.actor)
            adapter.post(inbox.iri, data=data, auth=auth)
            recipient.send = True
            recipient.save()
        except Exception as e:
            print(e)
            logger.error(f"Error in publish_to_recipient: {type(e).__name__}: {str(e)}", exc_info=True)
            raise


@receiver([post_save])
def publish_activity(sender, instance, **kwargs):
    try:
        if (
            isinstance(instance, Activity)
            and not isinstance(instance, Publish)
            and kwargs['created']
            and instance.is_local
        ):
            for recipient in instance.default_recipients:
                Recipient.objects.get_or_create(
                    actor=recipient,
                    activity=instance,
                )
            adapter.publish(instance)
    except Exception as e:
        logger.error(f"Failed to publish activity: {str(e)}", exc_info=True)


@receiver(post_save, sender=Publish)
def auto_adopt_event(sender, instance, created, **kwargs):
    try:
        if not instance.is_local and created:
            try:
                follow = Follow.objects.get(object=instance.actor)

                if follow.adoption_mode == 'LinkAdoptionMode':
                    adapter.link(instance.object)
            except Follow.DoesNotExist:
                logger.debug(f"No follow found for actor: {instance.actor}")
    except Exception as e:
        logger.error(f"Failed to auto-adopt event: {str(e)}")


@receiver(post_save, sender=Update)
def update_event(sender, instance, created, **kwargs):
    from bluebottle.activity_pub.serializers.json_ld import EventSerializer
    try:
        if not instance.is_local and created:
            try:
                follow = Follow.objects.get(object=instance.actor)

                if follow.adoption_mode == 'LinkAdoptionMode':
                    serializer = EventSerializer(
                        instance=instance.object, data=adapter.fetch(instance.object.iri)
                    )
                    serializer.is_valid(raise_exception=True)
                    event = serializer.save()

                    link = LinkedActivity.objects.get(event=event)

                    adapter.link(event, instance=link)
            except Follow.DoesNotExist:
                logger.debug(f"No follow found for actor: {instance.actor}")
    except Exception as e:
        logger.error(f"Failed to auto-adopt event: {str(e)}")

@receiver([post_save])
def create_organization(sender, instance, **kwargs):
    try:
        if isinstance(instance, Organization) and kwargs['created'] and not instance.organization_id:
            from bluebottle.activity_pub.serializers.federated_activities import (
                OrganizationSerializer as FederatedOrganizationSerializer
            )

            from bluebottle.activity_pub.serializers.json_ld import (
                OrganizationSerializer
            )
            data = OrganizationSerializer(instance=instance).data
            serializer = FederatedOrganizationSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            organization = serializer.save()
            instance.organization = organization
            instance.save(update_fields=['organization'])

    except Exception as e:
        logger.error(f"Failed to create related organization: {str(e)}")
