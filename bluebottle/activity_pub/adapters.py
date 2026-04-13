import logging
from io import BytesIO

import requests
from celery import shared_task
from django.db import connection
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_tools.middlewares.ThreadLocal import get_current_user
from requests_http_signature import HTTPSignatureAuth, algorithms

from bluebottle.activity_pub.authentication import key_resolver
from bluebottle.activity_pub.models import (
    Organization, Recipient, Follow, Create, Event, Finish, Cancel, Start
)
from bluebottle.activity_pub.parsers import JSONLDParser
from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.activity_pub.clients import client
from bluebottle.activity_pub.serializers.base import (
    ActivityPubSerializer, FederatedObjectSerializer
)
from bluebottle.activity_pub.utils import get_platform_actor, is_local
from bluebottle.clients.utils import LocalTenant
from bluebottle.webfinger.client import client as webfinger_client


logger = logging.getLogger(__name__)


class JSONLDAdapter():
    def follow(self, url, model=None):
        discovered_url = webfinger_client.get(url)
        data = client.fetch(discovered_url)

        serializer = ActivityPubSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        actor = serializer.save()
        if model:
            model.object = actor
        else:
            return Follow.objects.create(object=actor)

    def adopt(self, event, request):
        data = ActivityPubSerializer(instance=event, full=True).data
        serializer = FederatedObjectSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        follow = Follow.objects.get(object=event.source)
        organization = Create.objects.filter(object=event).first().actor.organization
        owner = follow.default_owner or get_current_user()
        return serializer.save(owner=owner, host_organization=organization, origin=event)

    def link(self, event, request=None):
        from bluebottle.activity_links.serializers import LinkedActivitySerializer

        data = ActivityPubSerializer(instance=event).data
        linked_activity = event.linked_activity
        serializer = LinkedActivitySerializer(
            data=data,
            instance=linked_activity,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        organization = Create.objects.filter(object=event).first().actor.organization

        save_kwargs = {
            'host_organization': organization,
            'event': event
        }

        return serializer.save(**save_kwargs)

    def create_or_update_event(self, activity):
        from bluebottle.activities.models import Activity as BluebottleActivity

        if not isinstance(activity, BluebottleActivity):
            raise TypeError('Activity must be a BluebottleActivity')

        try:
            instance = activity.origin
        except Event.DoesNotExist:
            instance = None


        federated_serializer = FederatedObjectSerializer(activity)

        serializer = ActivityPubSerializer(
            data=federated_serializer.data, instance=instance, origin=activity
        )
        serializer.is_valid(raise_exception=True)
        event = serializer.save()

        if not event.create_set.exists():
            Create.objects.create(actor=get_platform_actor(), object=event)

        return event


adapter = JSONLDAdapter()


@shared_task(
    autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5},
    name="bluebottle.activity_pub.adapters.publish_activities"
)
def publish_activities(recipient, activities, tenant):
    with LocalTenant(tenant, clear_tenant=True):
        for activity in activities:
            if not hasattr(activity, 'origin'):
                adapter.create_or_update_event(activity)

            publish = activity.origin.create_set.first()
            Recipient.objects.get_or_create(actor=recipient, activity=publish)


@shared_task(
    autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5},
    name="bluebottle.activity_pub.adapters.publish_to_recipient"
)
def publish_to_recipient(recipient, tenant):
    with LocalTenant(tenant, clear_tenant=True):
        activity = recipient.activity
        actor = recipient.actor
        inbox = getattr(actor, "inbox", None)

        if not activity.is_local:
            raise TypeError('Only local activities can be published')

        if recipient.send:
            raise TypeError('Already published activity to actor')

        if inbox is None or inbox.is_local:
            logger.warning(f"Actor {actor} has no inbox, skipping publish")
            pass

        try:
            data = ActivityPubSerializer().to_representation(activity)
            auth = client.get_auth(activity.actor)
            client.post(inbox.iri, data=data, auth=auth)
            recipient.send = True
            recipient.save()

            if isinstance(activity, Create):
                if activity.object.federated_object.status in ('open', 'granted', ):
                    Start.objects.create(object=activity.object)
                elif activity.object.federated_object.status == 'succeeded':
                    Finish.objects.create(object=activity.object)
                else:
                    Cancel.objects.create(object=activity.object)

        except Exception as e:
            print(f"Error in publish_to_recipient: {type(e).__name__}: {str(e)}", exc_info=True)
            logger.error(f"Error in publish_to_recipient: {type(e).__name__}: {str(e)}", exc_info=True)
            raise


@receiver(post_save, sender=Recipient)
def publish_recipient(instance, created, **kwargs):
    if created:
        publish_to_recipient.delay(instance, connection.tenant)

        # Sometimes we need to send follow up activities to the recipient,
        # for example when the activity transitioned before the recipient was created
        for transition_cls in [Start, Finish, Cancel]:
            if isinstance(instance.activity, Create):
                for transition in transition_cls.objects.filter(object=instance.activity.object):
                    Recipient.objects.get_or_create(
                        actor=instance.actor,
                        activity=transition
                    )


@receiver([post_save])
def create_organization(sender, instance, **kwargs):
    try:
        if isinstance(instance, Organization) and kwargs['created'] and not instance.federated_object_id:
            data = ActivityPubSerializer(instance=instance).data
            serializer = FederatedObjectSerializer(data=data, origin=instance)
            serializer.is_valid(raise_exception=True)
            serializer.save()

    except Exception as e:
        logger.error(f"Failed to create related organization: {str(e)}")
