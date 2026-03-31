import logging
from io import BytesIO

import requests
from celery import shared_task
from django.db import connection
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import now
from django_tools.middlewares.ThreadLocal import get_current_user
from requests_http_signature import HTTPSignatureAuth, algorithms

from bluebottle.activity_pub.authentication import key_resolver
from bluebottle.activity_pub.models import (
    Organization, Recipient, Follow, Create, Event, Finish, Cancel, Start,
    Join, Leave, Update, GoodDeed, DoGoodEvent, SubEvent
)
from bluebottle.activity_pub.parsers import JSONLDParser
from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.activity_pub.utils import get_platform_actor, is_local
from bluebottle.clients.utils import LocalTenant
from bluebottle.webfinger.client import client

logger = logging.getLogger(__name__)


def _joined_participant_status(activity):
    from bluebottle.time_based.models import DeadlineActivity

    if isinstance(activity, DeadlineActivity):
        if not activity.start or activity.start < now().date():
            return 'succeeded'
        return 'accepted'
    return 'accepted'


def _joined_date_participant_status(slot):
    from django.utils import timezone as django_tz

    if slot is None:
        return 'accepted'
    end = slot.end
    if end is not None and end < django_tz.now():
        return 'succeeded'
    return 'accepted'


def _resolve_date_activity_slot_for_sync(activity, sub_event_id):
    from bluebottle.time_based.models import DateActivity, DateActivitySlot

    if not isinstance(activity, DateActivity):
        return None
    if sub_event_id:
        return DateActivitySlot.objects.filter(activity=activity, origin_id=sub_event_id).first()
    if activity.slots.count() == 1:
        return activity.slots.first()
    return None


def resolve_sub_event_for_synced_date_join(participant, date_activity):
    """
    SubEvent on date_activity.origin (source DoGoodEvent) to target with Join/Leave.

    Adopted DateActivitySlots should set origin to that SubEvent; when origin is missing or
    points at another event, match by start_time (or single-slot fallback) so the source
    platform can resolve the correct DateActivitySlot.
    """
    from bluebottle.activity_pub.models import DoGoodEvent, SubEvent
    from bluebottle.time_based.models import DateActivity, DateParticipant

    if not isinstance(participant, DateParticipant) or not isinstance(date_activity, DateActivity):
        return None
    origin_event = getattr(date_activity, 'origin', None)
    if not isinstance(origin_event, DoGoodEvent):
        return None
    slot = participant.slot
    if slot is None:
        return None
    origin_id = getattr(slot, 'origin_id', None)
    if origin_id:
        try:
            sub = SubEvent.objects.get(pk=origin_id)
        except SubEvent.DoesNotExist:
            sub = None
        if sub is not None and sub.parent_id == origin_event.pk:
            return sub
    if slot.start is not None:
        qs = origin_event.sub_event.filter(start_time=slot.start)
        if slot.duration is not None:
            with_duration = [s for s in qs if s.duration == slot.duration]
            if len(with_duration) == 1:
                return with_duration[0]
        matched = list(qs)
        if len(matched) == 1:
            return matched[0]
    subs = list(origin_event.sub_event.order_by('start_time', 'id'))
    if len(subs) == 1:
        return subs[0]
    return None


def _sync_slot_from_subevent(instance):
    from bluebottle.activity_pub.serializers.federated_activities import SlotsSerializer
    from bluebottle.time_based.models import DateActivity

    parent = getattr(instance, 'parent', None)
    activity = getattr(parent, 'activity', None) if parent is not None else None
    if activity is None:
        return
    activity = activity.get_real_instance()
    if not isinstance(activity, DateActivity):
        return

    payload = {
        'name': instance.name,
        'start_time': instance.start_time,
        'duration': instance.duration,
        'capacity': instance.capacity,
        'contributor_count': instance.contributor_count or 0,
    }
    if instance.iri:
        payload['id'] = instance.iri
    if instance.event_attendance_mode is not None:
        payload['event_attendance_mode'] = instance.event_attendance_mode

    serializer = SlotsSerializer(
        data=payload,
        partial=True,
    )
    serializer.is_valid(raise_exception=True)
    slot = serializer.save(activity=activity)

    update_kwargs = {'capacity': slot.capacity}
    if instance.slot_id != slot.pk:
        update_kwargs['slot_id'] = slot.pk
    SubEvent.objects.filter(pk=instance.pk).update(**update_kwargs)


def _sync_adopted_date_slots_from_source(event_do_good, source_date, adopted_date):
    from bluebottle.activity_pub.serializers.federated_activities import (
        sync_adopted_date_slots_from_source,
    )
    sync_adopted_date_slots_from_source(event_do_good, source_date, adopted_date)


def _sync_adopted_activities_for_ap_object(obj, update=None):
    try:
        from bluebottle.activity_pub.serializers.update_sync import PolymorphicUpdateSyncSerializer

        serializer = PolymorphicUpdateSyncSerializer(
            context={'object': obj, 'adapter': adapter, 'update': update}
        )
        serializer.sync()
    except Exception as e:
        logger.error(
            f"Failed to sync adopted activities for {obj.__class__.__name__}: {str(e)}",
            exc_info=True,
        )


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
        Adopt a remote event into a local activity.
        For GoodDeed and DoGoodEvent, set origin=event so Updates sync to adopted activities and
        Join/Leave can target the source event.
        For other event types, keep backward-compatible adopt behavior (no origin kwarg).
        """
        from bluebottle.activity_pub.serializers.federated_activities import FederatedActivitySerializer
        from bluebottle.activity_pub.serializers.json_ld import EventSerializer
        from bluebottle.members.models import Member

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

        save_kwargs = {
            'owner': owner,
            'host_organization': organization,
        }
        if isinstance(event, (GoodDeed, DoGoodEvent)):
            save_kwargs['origin'] = event

        activity = serializer.save(**save_kwargs)
        self.create_or_update_event(activity)
        return activity

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

        if isinstance(event, (GoodDeed, DoGoodEvent)):
            sync_event_contributor_count(event)

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


def _activity_contributor_count(activity):
    if not activity:
        return 0

    if hasattr(activity, 'contributor_count'):
        return activity.contributor_count

    accepted = getattr(activity, 'accepted_participants', None)
    if accepted is not None:
        return accepted.count() + (getattr(activity, 'deleted_successful_contributors', 0) or 0)

    return 0


def sync_sub_event_contributor_counts(event):
    """
    Copy per-slot participant totals onto SubEvent rows for DoGoodEvent (date activities).
    Slots are resolved via DateActivitySlot.origin_id == SubEvent.pk (SubEvent.slot is often unset).
    """
    if not isinstance(event, DoGoodEvent):
        return
    activity = getattr(event, 'activity', None)
    if not activity:
        return
    from bluebottle.time_based.models import DateActivity, DateActivitySlot

    if not isinstance(activity, DateActivity):
        return
    event_sub_count = event.sub_event.count()
    activity_slot_count = activity.slots.count()

    for se in event.sub_event.all():
        slot = DateActivitySlot.objects.filter(activity=activity, origin_id=se.pk).first()
        if slot is None and se.slot_id:
            slot = se.slot
        if slot is None and se.start_time is not None:
            # Prefer matching an orphan slot by start (+ duration when available).
            qs = DateActivitySlot.objects.filter(activity=activity, start=se.start_time)
            if se.duration is not None:
                match = qs.filter(duration=se.duration).first()
                if match is not None:
                    slot = match
            if slot is None:
                slot = qs.first()
        if slot is None and event_sub_count == 1 and activity_slot_count == 1:
            slot = activity.slots.first()

        new_val = slot.contributor_count if slot else 0
        update_kwargs = {}
        if se.contributor_count != new_val:
            update_kwargs['contributor_count'] = new_val
        if slot is not None and se.slot_id != slot.pk:
            update_kwargs['slot_id'] = slot.pk
        if update_kwargs:
            SubEvent.objects.filter(pk=se.pk).update(**update_kwargs)

        # Backfill the slot -> SubEvent link too, so slot.origin is stable for joins/adoption.
        if slot is not None and slot.origin_id != se.pk:
            DateActivitySlot.objects.filter(pk=slot.pk).update(origin_id=se.pk)
        continue


def sync_event_contributor_count(event):
    """
    Set event.contributor_count from linked activity participants for sync-capable events.
    Currently supports GoodDeed (deed) and DoGoodEvent (deadline activity).
    """
    if not isinstance(event, (GoodDeed, DoGoodEvent)):
        return
    activity = getattr(event, 'activity', None)
    new_total = _activity_contributor_count(activity)
    if event.contributor_count != new_total:
        event.contributor_count = new_total
        event.save(update_fields=['contributor_count'])
    if isinstance(event, DoGoodEvent):
        sync_sub_event_contributor_counts(event)


def sync_good_deed_contributor_count(event):
    # Backward-compatible wrapper kept for existing call sites/tests.
    sync_event_contributor_count(event)


@receiver(post_save, sender=Join)
def handle_join_received(sender, instance, created, **kwargs):
    """On receiving a Join: add participant to source synced activity and broadcast Update."""
    if not created or instance.is_local:
        return
    try:
        event = instance.object
        if not isinstance(event, (GoodDeed, DoGoodEvent)):
            return

        activity = getattr(event, 'activity', None)
        if activity and instance.participant_sync_id:
            from bluebottle.activities.models import RemoteContributor
            from bluebottle.deeds.models import Deed, DeedParticipant
            from bluebottle.time_based.models import (
                DateActivity,
                DateParticipant,
                DeadlineActivity,
                DeadlineParticipant,
            )

            participant_model = None
            date_slot = None
            if isinstance(activity, Deed):
                participant_model = DeedParticipant
            elif isinstance(activity, DeadlineActivity):
                participant_model = DeadlineParticipant
            elif isinstance(activity, DateActivity):
                participant_model = DateParticipant
                date_slot = _resolve_date_activity_slot_for_sync(activity, instance.sub_event_id)
                if date_slot is None:
                    logger.warning(
                        'Join for DateActivity could not resolve slot (sub_event=%s, activity=%s)',
                        instance.sub_event_id,
                        activity.pk,
                    )
                    return
            else:
                return

            existing_query = participant_model.objects.filter(
                activity=activity,
                remote_contributor__sync_id=instance.participant_sync_id,
                remote_contributor__sync_actor=instance.actor,
            )
            if date_slot is not None:
                existing_query = existing_query.filter(slot=date_slot)
            existing = existing_query.first()
            if isinstance(activity, DateActivity):
                target_status = _joined_date_participant_status(date_slot)
            else:
                target_status = _joined_participant_status(activity)
            if existing:
                # Re-join after withdraw: set status back to accepted and refresh name/email
                if existing.status != target_status:
                    existing.status = target_status
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
                remote_contributor, _ = RemoteContributor.objects.get_or_create(
                    sync_actor=sync_actor,
                    sync_id=instance.participant_sync_id,
                    defaults={
                        'display_name': instance.participant_name or '',
                        'email': instance.participant_email,
                    },
                )

                create_kwargs = dict(
                    activity=activity,
                    user=None,
                    remote_contributor=remote_contributor,
                    status=target_status,
                )
                if date_slot is not None:
                    create_kwargs['slot'] = date_slot
                participant_model.objects.create(**create_kwargs)

        sync_event_contributor_count(event)
        Update.objects.create(object=event)
    except Exception as e:
        logger.error(f"Failed to handle Join: {str(e)}", exc_info=True)


@receiver(post_save, sender=Leave)
def handle_leave_received(sender, instance, created, **kwargs):
    """On receiving a Leave: reject matching synced participant, update count, broadcast Update."""
    if not created or instance.is_local:
        return
    try:
        event = instance.object
        if not isinstance(event, (GoodDeed, DoGoodEvent)):
            return

        # Resolve target deed based on direction:
        # - If Leave is sent by a follower, we're the source -> update event.activity.
        # - If Leave is sent by the source actor, we're a follower -> update adopted activity.
        source_actor = getattr(event, 'source', None)
        activity = None
        if source_actor is not None and instance.actor_id == source_actor.pk:
            activity = event.adopted_activities.first()
        if activity is None:
            activity = getattr(event, 'activity', None)
        if activity is None and hasattr(event, 'adopted_activities'):
            activity = event.adopted_activities.first()
        if activity and instance.participant_sync_id:
            from bluebottle.activities.models import Contributor
            from bluebottle.time_based.models import DateActivity, DateParticipant

            contributor = None
            if isinstance(activity, DateActivity):
                date_slot = _resolve_date_activity_slot_for_sync(activity, instance.sub_event_id)
                qs = DateParticipant.objects.filter(
                    activity=activity,
                    remote_contributor__sync_id=instance.participant_sync_id,
                    remote_contributor__sync_actor=instance.actor,
                )
                if date_slot is not None:
                    qs = qs.filter(slot=date_slot)
                elif activity.slots.count() > 1:
                    qs = qs.none()
                contributor = qs.first()
            else:
                contributor = Contributor.objects.filter(
                    activity=activity,
                    remote_contributor__sync_id=instance.participant_sync_id,
                    remote_contributor__sync_actor=instance.actor,
                ).first()
            if contributor:
                # Contract: any remote leave-like transition maps to rejected.
                contributor.status = 'rejected'
                contributor.save(update_fields=['status'])

        local_event = getattr(activity, 'event', None) if activity else None
        if local_event and isinstance(local_event, (GoodDeed, DoGoodEvent)):
            sync_event_contributor_count(local_event)
            Update.objects.create(object=local_event)
        else:
            sync_event_contributor_count(event)
            Update.objects.create(object=event)
    except Exception as e:
        logger.error(f"Failed to handle Leave: {str(e)}", exc_info=True)


@receiver(post_save, sender=Update)
def handle_update_received(sender, instance, created, **kwargs):
    """When an Update is created for a synced object, sync adopted activities."""
    if not created:
        return
    obj = instance.object
    if obj is None:
        return
    _sync_adopted_activities_for_ap_object(obj, update=instance)


@receiver(post_save, sender=SubEvent)
def handle_subevent_saved(sender, instance, **kwargs):
    try:
        _sync_slot_from_subevent(instance)
    except Exception as e:
        logger.error(f"Failed to sync DateActivitySlot for SubEvent: {str(e)}", exc_info=True)


@receiver(post_save)
def handle_deed_participant_change(sender, instance, **kwargs):
    """When synced deed/deadline participant changes, sync origin event contributor_count."""
    from bluebottle.deeds.models import DeedParticipant
    from bluebottle.time_based.models import DeadlineParticipant, DateParticipant
    if not isinstance(instance, (DeedParticipant, DeadlineParticipant, DateParticipant)):
        return
    try:
        deed = getattr(instance, 'activity', None)
        if not deed or not getattr(deed, 'origin_id', None) or not deed.origin_id:
            return
        origin = getattr(deed, 'origin', None)
        if not origin or not isinstance(origin, (GoodDeed, DoGoodEvent)):
            return
        sync_event_contributor_count(origin)
    except Exception as e:
        logger.error(f"Failed to sync contributor_count for DeedParticipant: {str(e)}", exc_info=True)


@receiver(post_delete)
def handle_deed_participant_delete(sender, instance, **kwargs):
    """When synced deed/deadline participant is deleted, sync origin event contributor_count."""
    from bluebottle.deeds.models import DeedParticipant
    from bluebottle.time_based.models import DeadlineParticipant, DateParticipant
    if not isinstance(instance, (DeedParticipant, DeadlineParticipant, DateParticipant)):
        return
    try:
        deed = getattr(instance, 'activity', None)
        if not deed or not getattr(deed, 'origin_id', None) or not deed.origin_id:
            return
        origin = getattr(deed, 'origin', None)
        if not origin or not isinstance(origin, (GoodDeed, DoGoodEvent)):
            return
        sync_event_contributor_count(origin)
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
