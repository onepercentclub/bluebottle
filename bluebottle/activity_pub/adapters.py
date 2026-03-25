import logging
from io import BytesIO

import requests
from celery import shared_task
from django.db import connection
from django.db.models.signals import post_save, post_delete, pre_save
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
            data=federated_serializer.data,
            instance=instance,
            context={'internal_update': True},
        )
        serializer.is_valid(raise_exception=True)
        event = serializer.save(activity=activity)

        if not event.create_set.exists():
            Create.objects.create(actor=get_platform_actor(), object=event)

        if isinstance(event, GoodDeed):
            sync_good_deed_contributor_count(event)

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
        for transition_cls in [Start, Finish, Cancel]:
            if isinstance(instance.activity, Create):
                for transition in transition_cls.objects.filter(object=instance.activity.object):
                    Recipient.objects.get_or_create(
                        actor=instance.actor,
                        activity=transition
                    )


def sync_good_deed_contributor_count(event):
    """
    Set GoodDeed.contributor_count from linked Deed's contributor_count.
    Call when the Deed's participants change (Join/Leave or local add/remove).
    """
    if not isinstance(event, GoodDeed):
        return
    deed = getattr(event, 'activity', None)
    new_total = deed.contributor_count if deed else 0
    if event.contributor_count != new_total:
        event.contributor_count = new_total
        event.save(update_fields=['contributor_count'])


@receiver(post_save, sender=Join)
def handle_join_received(sender, instance, created, **kwargs):
    """On receiving a Join: add participant to source deed, sync total, broadcast Update(GoodDeed)."""
    if not created or instance.is_local:
        return
    try:
        event = instance.object
        if not isinstance(event, GoodDeed):
            return

        # Add participant to source platform's deed (full list with name/email, and which Actor/Follow it came from)
        deed = getattr(event, 'activity', None)
        if deed and instance.participant_sync_id:
            from bluebottle.activities.models import RemoteContributor
            from bluebottle.deeds.models import DeedParticipant
            from bluebottle.activity_pub.models import Follow

            existing = DeedParticipant.objects.filter(
                activity=deed, remote_contributor__sync_id=instance.participant_sync_id
            ).first()
            if existing:
                # Re-join after withdraw: set status back to accepted and refresh name/email
                if existing.status != 'accepted':
                    existing.status = 'accepted'
                    existing.save(update_fields=['status'])
                rc = existing.remote_contributor
                if rc and (instance.participant_name is not None or instance.participant_email is not None):
                    if instance.participant_name is not None:
                        rc.display_name = instance.participant_name or ''
                        rc.save(update_fields=['display_name'])
                    if instance.participant_email is not None:
                        rc.email = instance.participant_email
                        rc.save(update_fields=['email'])
            else:
                sync_actor = instance.actor
                sync_follow = Follow.objects.filter(object=sync_actor).first()
                remote_contributor, created_rc = RemoteContributor.objects.get_or_create(
                    sync_id=instance.participant_sync_id,
                    defaults={
                        'display_name': instance.participant_name or '',
                        'email': instance.participant_email,
                        'sync_actor': sync_actor,
                        'sync_follow': sync_follow,
                    },
                )
                if not created_rc:
                    update_fields = []
                    if remote_contributor.sync_actor_id is None:
                        remote_contributor.sync_actor = sync_actor
                        update_fields.append('sync_actor')
                    if remote_contributor.sync_follow_id is None:
                        remote_contributor.sync_follow = sync_follow
                        update_fields.append('sync_follow')
                    if instance.participant_name is not None and remote_contributor.display_name != (instance.participant_name or ''):
                        remote_contributor.display_name = instance.participant_name or ''
                        update_fields.append('display_name')
                    if instance.participant_email is not None and remote_contributor.email != instance.participant_email:
                        remote_contributor.email = instance.participant_email
                        update_fields.append('email')
                    if update_fields:
                        remote_contributor.save(update_fields=update_fields)

                DeedParticipant.objects.create(
                    activity=deed,
                    user=None,
                    remote_contributor=remote_contributor,
                    status='accepted',
                )

        sync_good_deed_contributor_count(event)
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

        # Resolve target deed based on direction:
        # - If Leave is sent by a follower, we're the source -> update event.activity.
        # - If Leave is sent by the source actor, we're a follower -> update adopted deed.
        source_actor = getattr(event, 'source', None)
        deed = None
        if source_actor is not None and instance.actor_id == source_actor.pk:
            deed = event.adopted_activities.first()
        if deed is None:
            deed = getattr(event, 'activity', None)
        if deed is None and hasattr(event, 'adopted_activities'):
            deed = event.adopted_activities.first()
        if deed and instance.participant_sync_id:
            from bluebottle.activities.models import Contributor

            contributor = Contributor.objects.filter(
                activity=deed,
                remote_contributor__sync_id=instance.participant_sync_id,
            ).first()
            if contributor:
                # Contract: any remote leave-like transition maps to rejected.
                contributor.status = 'rejected'
                contributor.save(update_fields=['status'])

        local_event = getattr(deed, 'event', None) if deed else None
        if local_event and isinstance(local_event, GoodDeed):
            sync_good_deed_contributor_count(local_event)
            Update.objects.create(object=local_event)
        else:
            sync_good_deed_contributor_count(event)
            Update.objects.create(object=event)
    except Exception as e:
        logger.error(f"Failed to handle Leave: {str(e)}", exc_info=True)


@receiver(post_save, sender=Update)
def handle_update_received(sender, instance, created, **kwargs):
    """When an Update is received for a GoodDeed, update the canonical event and sync adopted deeds' local GoodDeed."""
    if not created or not isinstance(instance.object, GoodDeed):
        return
    try:
        event = instance.object
        from bluebottle.deeds.models import Deed

        for activity in event.adopted_activities.all():
            if not isinstance(activity, Deed):
                continue
            deed = activity
            # Copy updated fields from the event to the deed so create_or_update_event has current data
            update_fields = []
            if event.name != deed.title:
                deed.title = event.name
                update_fields.append('title')
            if getattr(event, 'start_time', None) is not None and deed.start != event.start_time.date():
                deed.start = event.start_time.date()
                update_fields.append('start')
            if getattr(event, 'end_time', None) is not None and deed.end != event.end_time.date():
                deed.end = event.end_time.date()
                update_fields.append('end')
            if event.summary is not None:
                try:
                    if getattr(deed.description, 'html', None) != event.summary:
                        if hasattr(deed.description, 'html'):
                            deed.description.html = event.summary
                            update_fields.append('description')
                except (AttributeError, TypeError):
                    pass
            if update_fields:
                deed.save(update_fields=update_fields)
            # Sync the deed's local GoodDeed (deed.event) from the deed's current data
            adapter.create_or_update_event(deed)
    except Exception as e:
        logger.error(f"Failed to handle Update for GoodDeed: {str(e)}", exc_info=True)


@receiver(post_save)
def handle_deed_participant_change(sender, instance, **kwargs):
    """When Deed gains/loses a participant, sync GoodDeed.contributor_count from Deed.contributor_count."""
    from bluebottle.deeds.models import DeedParticipant
    if not isinstance(instance, DeedParticipant):
        return
    try:
        deed = getattr(instance, 'activity', None)
        if not deed or not getattr(deed, 'origin_id', None) or not deed.origin_id:
            return
        origin = getattr(deed, 'origin', None)
        if not origin or not isinstance(origin, GoodDeed):
            return
        sync_good_deed_contributor_count(origin)
    except Exception as e:
        logger.error(f"Failed to sync contributor_count for DeedParticipant: {str(e)}", exc_info=True)


@receiver(post_delete)
def handle_deed_participant_delete(sender, instance, **kwargs):
    """When a DeedParticipant is deleted, sync GoodDeed.contributor_count from Deed.contributor_count."""
    from bluebottle.deeds.models import DeedParticipant
    if not isinstance(instance, DeedParticipant):
        return
    try:
        deed = getattr(instance, 'activity', None)
        if not deed or not getattr(deed, 'origin_id', None) or not deed.origin_id:
            return
        origin = getattr(deed, 'origin', None)
        if not origin or not isinstance(origin, GoodDeed):
            return
        sync_good_deed_contributor_count(origin)
    except Exception as e:
        logger.error(f"Failed to sync contributor_count on DeedParticipant delete: {str(e)}", exc_info=True)


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
