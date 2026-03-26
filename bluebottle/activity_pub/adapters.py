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
    Join, Leave, Update, GoodDeed, DoGoodEvent
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


def _source_date_slot_for_sub_event(sub_event, source_date):
    from bluebottle.time_based.models import DateActivitySlot

    if source_date is None:
        return None
    if sub_event.slot_id:
        slot = sub_event.slot
        if slot is not None and getattr(slot, 'activity_id', None) == source_date.pk:
            return slot
    return DateActivitySlot.objects.filter(activity=source_date, origin=sub_event).first()


def _is_online_from_sub_event(sub):
    if sub.event_attendance_mode == 'OnlineEventAttendanceMode':
        return True
    if sub.event_attendance_mode == 'OfflineEventAttendanceMode':
        return False
    return None


def _adopted_slot_has_active_participants(slot):
    return slot.participants.filter(
        status__in=['new', 'accepted', 'succeeded', 'scheduled', 'participating'],
    ).exists()


def _sync_adopted_date_slots_from_source(event_do_good, source_date, adopted_date):
    from bluebottle.time_based.models import DateActivitySlot

    slot_field_names = (
        'title',
        'capacity',
        'start',
        'duration',
        'is_online',
        'online_meeting_url',
        'location_id',
        'location_hint',
        'status',
    )
    sub_only_field_names = (
        'title',
        'capacity',
        'start',
        'duration',
        'is_online',
    )
    subs = list(event_do_good.sub_event.order_by('start_time', 'id'))
    if not subs and source_date is not None and source_date.slots.exists():
        return

    if subs:
        known_sub_ids = {s.pk for s in subs}
        for loose in adopted_date.slots.exclude(origin_id__in=known_sub_ids).exclude(
            origin_id__isnull=True
        ):
            loose.origin = None
            loose.save(update_fields=['origin'])

    for sub in subs:
        src_slot = _source_date_slot_for_sub_event(sub, source_date)
        start_for_match = src_slot.start if src_slot is not None else sub.start_time
        ad_slot = DateActivitySlot.objects.filter(activity=adopted_date, origin=sub).first()
        if ad_slot is None and src_slot is not None:
            ad_slot = DateActivitySlot.objects.filter(
                activity=adopted_date,
                origin__isnull=True,
                start=src_slot.start,
            ).first()
        if ad_slot is None and start_for_match is not None:
            ad_slot = DateActivitySlot.objects.filter(
                activity=adopted_date,
                origin__isnull=True,
                start=start_for_match,
            ).first()
        if ad_slot is None and len(subs) == 1:
            orphans = list(
                adopted_date.slots.filter(origin__isnull=True)
            )
            if len(orphans) == 1:
                ad_slot = orphans[0]
        if ad_slot is not None and ad_slot.origin_id != sub.pk:
            ad_slot.origin = sub
            ad_slot.save(update_fields=['origin'])
        if ad_slot is None:
            if src_slot is not None:
                DateActivitySlot.objects.create(
                    activity=adopted_date,
                    origin=sub,
                    title=src_slot.title,
                    capacity=src_slot.capacity,
                    start=src_slot.start,
                    duration=src_slot.duration,
                    is_online=src_slot.is_online,
                    online_meeting_url=src_slot.online_meeting_url,
                    location_id=src_slot.location_id,
                    location_hint=src_slot.location_hint,
                    status=src_slot.status,
                )
            else:
                DateActivitySlot.objects.create(
                    activity=adopted_date,
                    origin=sub,
                    title=sub.name,
                    capacity=sub.capacity,
                    start=sub.start_time,
                    duration=sub.duration,
                    is_online=_is_online_from_sub_event(sub),
                    online_meeting_url='',
                    location_id=None,
                    location_hint=None,
                    status='open',
                )
            continue
        update_fields = []
        if src_slot is not None:
            for field_name in slot_field_names:
                src_val = getattr(src_slot, field_name)
                if getattr(ad_slot, field_name) != src_val:
                    setattr(ad_slot, field_name, src_val)
                    update_fields.append(field_name)
        else:
            for field_name in sub_only_field_names:
                if field_name == 'title':
                    src_val = sub.name
                elif field_name == 'capacity':
                    src_val = sub.capacity
                elif field_name == 'start':
                    src_val = sub.start_time
                elif field_name == 'duration':
                    src_val = sub.duration
                elif field_name == 'is_online':
                    src_val = _is_online_from_sub_event(sub)
                else:
                    continue
                if getattr(ad_slot, field_name) != src_val:
                    setattr(ad_slot, field_name, src_val)
                    update_fields.append(field_name)
        if update_fields:
            ad_slot.save(update_fields=update_fields)

    for orphan in adopted_date.slots.filter(origin__isnull=True):
        if _adopted_slot_has_active_participants(orphan):
            continue
        orphan.delete()


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
    for se in event.sub_event.all():
        slot = DateActivitySlot.objects.filter(activity=activity, origin_id=se.pk).first()
        new_val = slot.contributor_count if slot else 0
        if se.contributor_count != new_val:
            se.contributor_count = new_val
            se.save(update_fields=['contributor_count'])


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
    """When an Update is created for a synced event, push field changes to adopted activities on this tenant."""
    if not created:
        return
    object_id = instance.object_id
    event_good_deed = GoodDeed.objects.filter(pk=object_id).first()
    if event_good_deed is not None:
        try:
            from bluebottle.deeds.models import Deed

            for activity in event_good_deed.adopted_activities.all():
                activity = activity.get_real_instance()
                if not isinstance(activity, Deed):
                    continue
                deed = activity
                update_fields = []
                if event_good_deed.name != deed.title:
                    deed.title = event_good_deed.name
                    update_fields.append('title')
                if getattr(event_good_deed, 'start_time', None) is not None and deed.start != event_good_deed.start_time.date():
                    deed.start = event_good_deed.start_time.date()
                    update_fields.append('start')
                if getattr(event_good_deed, 'end_time', None) is not None and deed.end != event_good_deed.end_time.date():
                    deed.end = event_good_deed.end_time.date()
                    update_fields.append('end')
                if event_good_deed.summary is not None:
                    try:
                        if getattr(deed.description, 'html', None) != event_good_deed.summary:
                            if hasattr(deed.description, 'html'):
                                deed.description.html = event_good_deed.summary
                                update_fields.append('description')
                    except (AttributeError, TypeError):
                        pass
                if update_fields:
                    deed.save(update_fields=update_fields)
                adapter.create_or_update_event(deed)
        except Exception as e:
            logger.error(f"Failed to handle Update for GoodDeed: {str(e)}", exc_info=True)
        return
    event_do_good = DoGoodEvent.objects.filter(pk=object_id).first()
    if event_do_good is not None:
        try:
            from bluebottle.time_based.models import DateActivity

            source_date = None
            source_bb_activity = event_do_good.activity
            if source_bb_activity is not None:
                real = source_bb_activity.get_real_instance()
                if isinstance(real, DateActivity):
                    source_date = real

            for activity in event_do_good.adopted_activities.all():
                activity = activity.get_real_instance()
                if not isinstance(activity, DateActivity):
                    continue
                from bluebottle.activity_pub.models import Event as ActivityPubEvent

                try:
                    adopted_ev = activity.event
                except ActivityPubEvent.DoesNotExist:
                    adopted_ev = None
                if adopted_ev is not None and event_do_good.capacity != adopted_ev.capacity:
                    adopted_ev.capacity = event_do_good.capacity
                    adopted_ev.save(update_fields=['capacity'])
                cap = event_do_good.capacity
                if cap is not None and cap != activity.capacity:
                    activity.capacity = cap
                    activity.save(update_fields=['capacity'])
                elif source_date is not None and source_date.capacity != activity.capacity:
                    activity.capacity = source_date.capacity
                    activity.save(update_fields=['capacity'])
                if event_do_good.name != activity.title:
                    activity.title = event_do_good.name
                    activity.save(update_fields=['title'])
                if event_do_good.summary is not None:
                    try:
                        if getattr(activity.description, 'html', None) != event_do_good.summary:
                            if hasattr(activity.description, 'html'):
                                activity.description.html = event_do_good.summary
                                activity.save(update_fields=['description'])
                    except (AttributeError, TypeError):
                        pass
                _sync_adopted_date_slots_from_source(
                    event_do_good, source_date, activity
                )
                adapter.create_or_update_event(activity)
        except Exception as e:
            logger.error(f"Failed to handle Update for DoGoodEvent: {str(e)}", exc_info=True)


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
