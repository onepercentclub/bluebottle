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
    Organization, Recipient, Follow, Create, Event, Finish, Cancel, Start,
    Join, Leave, Update, GoodDeed
)
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

    def follow(self, url, model=None):
        from bluebottle.activity_pub.serializers.json_ld import OrganizationSerializer

        discovered_url = client.get(url)
        data = self.fetch(discovered_url)

        serializer = OrganizationSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        actor = serializer.save()
        if model:
            model.object = actor
        else:
            return Follow.objects.create(object=actor)

    def clone(self, event, request):
        from bluebottle.activity_pub.serializers.federated_activities import FederatedActivitySerializer
        from bluebottle.activity_pub.serializers.json_ld import EventSerializer

        data = EventSerializer(instance=event, full=True).data
        serializer = FederatedActivitySerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        follow = Follow.objects.get(object=event.source)
        organization = Create.objects.filter(object=event).first().actor.organization
        owner = follow.default_owner or get_current_user()
        return serializer.save(owner=owner, host_organization=organization)

    def link(self, event, request=None):
        from bluebottle.activity_pub.serializers.json_ld import EventSerializer
        from bluebottle.activity_links.serializers import LinkedActivitySerializer

        data = EventSerializer(instance=event).data
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

    def adopt(self, event, request=None):
        """
        Create a fully synced local Deed from a remote GoodDeed (sync adoption).
        The Deed has origin=event so Join/Leave can target the source platform.
        """
        from bluebottle.activity_pub.models import GoodDeed
        from bluebottle.activity_pub.serializers.federated_activities import FederatedActivitySerializer
        from bluebottle.activity_pub.serializers.json_ld import EventSerializer
        from bluebottle.members.models import Member

        if not isinstance(event, GoodDeed):
            raise TypeError('adopt expects a GoodDeed event')

        create = Create.objects.filter(object=event).first()
        if not create:
            raise ValueError('No Create found for this event')
        follow = Follow.objects.get(object=create.actor)
        organization = create.actor.organization
        owner = follow.default_owner or get_current_user()
        if owner is None:
            owner = Member.objects.filter(is_active=True).first()
        if owner is None:
            raise ValueError(
                'Cannot adopt deed: no owner available. Set default_owner on the Follow or ensure a Member exists.'
            )

        context = {'request': request} if request is not None else {}
        data = EventSerializer(instance=event, full=True).data
        serializer = FederatedActivitySerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)

        deed = serializer.save(owner=owner, host_organization=organization, origin=event)
        self.create_or_update_event(deed)
        return deed

    def create_or_update_event(self, activity):
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
            if not hasattr(activity, 'event'):
                adapter.create_or_update_event(activity)

            publish = activity.event.create_set.first()
            Recipient.objects.get_or_create(actor=recipient, activity=publish)


@shared_task(
    autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5},
    name="bluebottle.activity_pub.adapters.publish_to_recipient"
)
def publish_to_recipient(recipient, tenant):
    from bluebottle.activity_pub.serializers.json_ld import ActivitySerializer
    with LocalTenant(tenant, clear_tenant=True):
        activity = recipient.activity
        actor = recipient.actor
        inbox = getattr(actor, "inbox", None)

        if not activity.is_local:
            raise TypeError('Only local activities can be published')

        if recipient.send:
            raise TypeError('Already published activity to actor')

        # For remote actors, fetch profile to get inbox URL if we don't have it stored
        inbox_url = None
        if inbox and getattr(inbox, 'iri', None) and not getattr(inbox, 'is_local', True):
            inbox_url = inbox.iri
        elif getattr(actor, 'iri', None) and is_local(actor.iri) is False:
            try:
                fetched = adapter.fetch(actor.iri)
                if fetched and isinstance(fetched, dict):
                    raw = fetched.get('inbox')
                    if isinstance(raw, str):
                        inbox_url = raw
                    elif isinstance(raw, dict):
                        inbox_url = raw.get('id') or raw.get('iri')
            except Exception as e:
                logger.warning(f"Could not fetch actor inbox for {actor.iri}: {e}")

        if not inbox_url:
            if inbox is None or getattr(inbox, 'is_local', True):
                logger.warning(f"Actor {actor} has no inbox (or local), skipping publish")
            return

        try:
            data = ActivitySerializer().to_representation(activity)
            auth = adapter.get_auth(activity.actor)
            adapter.post(inbox_url, data=data, auth=auth)
            recipient.send = True
            recipient.save()

            if isinstance(activity, Create):
                if activity.object.activity.status in ('open', 'granted', ):
                    Start.objects.create(object=activity.object)
                elif activity.object.activity.status == 'succeeded':
                    Finish.objects.create(object=activity.object)
                else:
                    Cancel.objects.create(object=activity.object)

        except Exception as e:
            logger.error(f"Error in publish_to_recipient: {type(e).__name__}: {str(e)}", exc_info=True)
            raise


@receiver(post_save, sender=Recipient)
def publish_recipient(instance, created, **kwargs):
    if created:
        publish_to_recipient.delay(instance, connection.tenant)

        # Sometimes we need to send follow up activities to the recipient,
        # for example when the activity transitioned before the recipient was created
        for transition_cls in [Finish, Cancel]:
            if isinstance(instance.activity, Create):
                for transition in transition_cls.objects.filter(object=instance.activity.object):
                    Recipient.objects.get_or_create(
                        actor=instance.actor,
                        activity=transition
                    )


@receiver(post_save, sender=Join)
def handle_join_received(sender, instance, created, **kwargs):
    """On receiving a Join: update synced count, add participant to source deed, broadcast Update(GoodDeed)."""
    if not created or instance.is_local:
        return
    try:
        event = instance.object
        if not isinstance(event, GoodDeed):
            return
        event.synced_participant_count = (event.synced_participant_count or 0) + 1
        event.save(update_fields=['synced_participant_count'])

        # Add participant to source platform's deed (full list with name/email, and which Actor/Follow it came from)
        deed = getattr(event, 'activity', None)
        if deed and instance.participant_sync_id:
            from bluebottle.deeds.models import DeedParticipant
            from bluebottle.activity_pub.models import Follow

            if not DeedParticipant.objects.filter(
                activity=deed, sync_id=instance.participant_sync_id
            ).exists():
                sync_actor = instance.actor
                sync_follow = Follow.objects.filter(object=sync_actor).first()

                DeedParticipant.objects.create(
                    activity=deed,
                    user=None,
                    display_name=instance.participant_name or '',
                    email=instance.participant_email,
                    sync_id=instance.participant_sync_id,
                    sync_actor=sync_actor,
                    sync_follow=sync_follow,
                    status='accepted',
                )

        Update.objects.create(object=event)
    except Exception as e:
        logger.error(f"Failed to handle Join: {str(e)}", exc_info=True)


@receiver(post_save, sender=Leave)
def handle_leave_received(sender, instance, created, **kwargs):
    """On receiving a Leave: remove matching participant, update count, broadcast Update(GoodDeed)."""
    if not created or instance.is_local:
        return
    try:
        event = instance.object
        if not isinstance(event, GoodDeed):
            return

        # Remove synced participant from source deed if we have a match
        deed = getattr(event, 'activity', None)
        if deed and instance.participant_sync_id:
            from bluebottle.activities.models import Contributor

            contributor = Contributor.objects.filter(
                activity=deed,
                sync_id=instance.participant_sync_id,
            ).first()
            if contributor:
                contributor.status = 'rejected'
                contributor.save(update_fields=['status'])

        event.synced_participant_count = max(0, (event.synced_participant_count or 0) - 1)
        event.save(update_fields=['synced_participant_count'])
        Update.objects.create(object=event)
    except Exception as e:
        logger.error(f"Failed to handle Leave: {str(e)}", exc_info=True)


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
