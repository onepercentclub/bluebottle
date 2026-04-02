import datetime
import logging
from io import BytesIO

import pytz
import requests
from django.contrib.gis.geos import Point
from django.core.files import File
from django.db import connection, models
from django.urls import reverse
from djmoney.money import Money
from rest_framework import exceptions
from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer

from bluebottle.activity_pub.models import EventAttendanceModeChoices, Image as ActivityPubImage, JoinModeChoices, \
    SubEvent, RepetitionModeChoices, SlotModeChoices
from bluebottle.activity_pub.serializers.base import FederatedObjectSerializer
from bluebottle.activity_pub.serializers.fields import FederatedIdField
from bluebottle.collect.models import CollectActivity, CollectType
from bluebottle.deeds.models import Deed
from bluebottle.files.models import Image
from bluebottle.files.serializers import ORIGINAL_SIZE
from bluebottle.funding.models import Funding
from bluebottle.geo.models import Country, Geolocation
from bluebottle.grant_management.models import GrantApplication
from bluebottle.organizations.models import Organization
from bluebottle.time_based.models import DateActivitySlot, DeadlineActivity, DateActivity, RegisteredDateActivity, \
    PeriodicActivity, ScheduleActivity
from bluebottle.utils.fields import RichTextField
from bluebottle.utils.models import get_default_language

logger = logging.getLogger(__name__)


class ImageSerializer(FederatedObjectSerializer):
    id = FederatedIdField('json-ld:image')
    url = serializers.SerializerMethodField()
    name = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    def get_url(self, instance):
        return connection.tenant.build_absolute_url(
            reverse('activity-image', args=(instance.activity_set.first().pk, ORIGINAL_SIZE))
        )

    def create(self, validated_data):
        if not validated_data:
            return None

        validated_data['owner'] = self.context['request'].user
        image = ActivityPubImage.objects.from_iri(validated_data['id'])

        response = requests.get(image.url, timeout=30)
        response.raise_for_status()

        validated_data['file'] = File(BytesIO(response.content), name=validated_data['name'])

        return super().create(validated_data)

    class Meta:
        model = Image
        fields = FederatedObjectSerializer.Meta.fields + (
            'url', 'name'
        )


class ImageField(serializers.Field):
    def to_internal_value(self, data):
        if not data:
            return None
        try:
            image = ActivityPubImage.objects.from_iri(data)
            image_url = image.url

            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            return File(BytesIO(response.content), name=image.name)
        except requests.exceptions.HTTPError as e:
            # If image is not found (404), log and return None since logo is an optional field
            if e.response.status_code == 404:
                logger.warning(f"Image not found (404) for IRI {data}, skipping logo field")
                return None
            # Re-raise other HTTP errors
            raise

    def to_representation(self, value):
        if not value:
            return None
        return value


class DateField(serializers.Field):
    def to_internal_value(self, data):
        try:
            return datetime.datetime.fromisoformat(data).date()
        except ValueError as e:
            raise exceptions.ValidationError(str(e))

    def to_representation(self, value):
        if isinstance(value, datetime.date):
            value = pytz.utc.localize(
                datetime.datetime(
                    value.year, value.month, value.day
                )
            )

        return value


class CountryField(serializers.CharField):
    def to_internal_value(self, data):
        result = super().to_internal_value(data)

        if result:
            try:
                return Country.objects.get(alpha2_code=result)
            except Country.DoesNotExist:
                raise exceptions.ValidationError(f'Unknown country code: {result}')


class AddressSerializer(FederatedObjectSerializer):
    id = FederatedIdField('json-ld:address')

    street_address = serializers.CharField(source='street', required=False, allow_null=True)
    postal_code = serializers.CharField(required=False, allow_null=True)

    locality = serializers.CharField(required=False, allow_null=True)
    region = serializers.CharField(source='province', required=False, allow_null=True)
    country = CountryField(source='country.code', required=False, allow_null=True)

    class Meta:
        model = Geolocation
        fields = (
            'id', 'street_address', 'postal_code', 'locality',
            'region', 'country'
        )

    def to_internal_value(self, data):
        if not data:
            return {}
        result = super().to_internal_value(data)
        del result['id']
        return result


class OrganizationSerializer(FederatedObjectSerializer):
    id = FederatedIdField('json-ld:organization')
    name = serializers.CharField(allow_null=True)
    summary = serializers.CharField(
        source='description',
        allow_blank=True,
        allow_null=True,
        required=False
    )
    icon = ImageField(source='logo', required=False, allow_null=True)

    class Meta:
        model = Organization
        fields = ('id', 'name', 'summary', 'icon')


class LocationSerializer(FederatedObjectSerializer):
    id = FederatedIdField('json-ld:place')
    latitude = serializers.FloatField(source='position.x', allow_null=True)
    longitude = serializers.FloatField(source='position.y', allow_null=True)
    name = serializers.CharField(source='formatted_address', allow_null=True)

    address = AddressSerializer(source='*', allow_null=True)

    class Meta:
        model = Geolocation
        fields = ('id', 'latitude', 'longitude', 'name', 'address',)

    def create(self, validated_data):
        if not validated_data:
            return None
        try:
            validated_data['country'] = validated_data['country']['code']
        except KeyError:
            pass

        try:
            validated_data['position'] = Point(
                float(validated_data['position']['x']),
                float(validated_data['position']['y'])
            )
        except KeyError:
            pass

        return super().create(validated_data)


class BaseFederatedActivitySerializer(FederatedObjectSerializer):
    name = serializers.CharField(source='title')
    summary = RichTextField(source='description', allow_blank=True, allow_null=True)
    image = ImageSerializer(required=False, allow_null=True)
    organization = OrganizationSerializer(required=False, allow_null=True)
    contributor_count = serializers.IntegerField(
        source='synced_contributor_count',
        required=False,
        allow_null=True,
    )
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return connection.tenant.build_absolute_url(
            obj.get_absolute_url()
        )

    class Meta(FederatedObjectSerializer.Meta):
        fields = FederatedObjectSerializer.Meta.fields + (
            'name', 'summary', 'image', 'organization', 'contributor_count', 'url'
        )

    def save(self, *args, **kwargs):
        if not kwargs.get('owner'):
            kwargs['owner'] = self.context['request'].user

        return super().save(**kwargs)


class FederatedDeedSerializer(BaseFederatedActivitySerializer):
    id = FederatedIdField('json-ld:good-deed')
    start_time = DateField(source='start', allow_null=True)
    end_time = DateField(source='end', allow_null=True)
    contributor_count = serializers.IntegerField(allow_null=True, read_only=True)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = Deed
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'start_time', 'end_time', 'contributor_count'
        )


class ParlerNameRelatedField(serializers.RelatedField):
    def __init__(self, *, name_field="name", create_if_missing=True, **kwargs):
        self.name_field = name_field
        self.create_if_missing = create_if_missing
        super().__init__(**kwargs)

    def to_representation(self, value):
        lang = get_default_language()
        translated = value.safe_translation_getter(
            self.name_field,
            language_code=lang,
            any_language=True,
        )
        return translated

    def to_internal_value(self, data):
        if data is None or data == "":
            return None
        if not isinstance(data, str):
            raise serializers.ValidationError("Expected a string.")

        lang = get_default_language()
        qs = self.get_queryset()
        if qs is None:
            raise serializers.ValidationError("No queryset provided for related field.")

        try:
            obj = qs.translated(lang, **{self.name_field: data}).get()
            return obj
        except qs.model.DoesNotExist:
            if not self.create_if_missing:
                raise serializers.ValidationError(f"Unknown {qs.model.__name__}: {data}")

        obj = qs.model()
        obj.set_current_language(lang)
        setattr(obj, self.name_field, data)
        obj.save()
        return obj


class FederatedCollectSerializer(BaseFederatedActivitySerializer):
    id = FederatedIdField('json-ld:collect-campaign')
    start_time = DateField(source='start', allow_null=True)
    end_time = DateField(source='end', allow_null=True)
    collect_type = ParlerNameRelatedField(
        queryset=CollectType.objects.all(),
        allow_null=True,
        required=False,
        create_if_missing=True,
    )
    target = serializers.FloatField(allow_null=True, required=False)
    donated = serializers.FloatField(source='realized', allow_null=True, required=False)
    location = LocationSerializer(allow_null=True, required=False)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = CollectActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'start_time', 'end_time',
            'collect_type', 'target', 'donated', 'realized',
            'location',
        )


class FederatedFundingSerializer(BaseFederatedActivitySerializer):
    id = FederatedIdField('json-ld:crowd-funding')

    location = LocationSerializer(source='impact_location', allow_null=True, required=False)

    end_time = serializers.DateTimeField(source='deadline')
    target = serializers.DecimalField(source='target.amount', decimal_places=2, max_digits=10)
    target_currency = serializers.CharField(source='target.currency')
    donated = serializers.DecimalField(source='amount_donated.amount', decimal_places=2, max_digits=10)
    donated_currency = serializers.CharField(source='amount_donated.currency')

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = Funding
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'location', 'end_time',
            'target', 'target_currency',
            'donated', 'donated_currency'
        )

    def create(self, validated_data):
        if validated_data.get('target'):
            validated_data['target'] = Money(
                **validated_data['target']
            )
        if validated_data.get('amount_donated'):
            validated_data['amount_donated'] = Money(
                **validated_data['amount_donated']
            )
        return super().create(validated_data)


class FederatedGrantApplicationSerializer(BaseFederatedActivitySerializer):
    id = FederatedIdField('json-ld:grant-application')

    location = LocationSerializer(source='impact_location', allow_null=True, required=False)

    start_time = serializers.DateTimeField(source='started', required=False, allow_null=True)
    target = serializers.DecimalField(
        source='target.amount',
        decimal_places=2,
        max_digits=10,
        required=False,
        allow_null=True,
    )
    target_currency = serializers.CharField(source='target.currency', required=False, allow_null=True)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = GrantApplication
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'location', 'start_time',
            'target', 'target_currency',
        )

    def create(self, validated_data):
        if validated_data.get('target'):
            validated_data['target'] = Money(
                **validated_data['target']
            )
        return super().create(validated_data)


class EventAttendanceModeField(serializers.Field):
    def __init__(self, *args, **kwargs):
        kwargs['source'] = 'is_online'
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        return (
            EventAttendanceModeChoices.online if value else EventAttendanceModeChoices.offline
        )

    def to_internal_value(self, value):
        if value == EventAttendanceModeChoices.online:
            return True
        elif value == EventAttendanceModeChoices.offline:
            return False


class JoinModeField(serializers.Field):
    def __init__(self, *args, **kwargs):
        kwargs['source'] = kwargs.get('source', 'review')
        kwargs['required'] = False
        kwargs['allow_null'] = True

        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        return (
            JoinModeChoices.review if value else JoinModeChoices.open
        )

    def to_internal_value(self, value):
        if value == JoinModeChoices.review:
            return True
        else:
            return False


class RepetitionModeField(serializers.Field):
    def __init__(self, *args, **kwargs):
        kwargs['source'] = kwargs.get('source', 'period')
        kwargs['required'] = False
        kwargs['allow_null'] = True

        super().__init__(*args, **kwargs)

    mapping = {
        'days': RepetitionModeChoices.daily,
        'weeks': RepetitionModeChoices.weekly,
        'months': RepetitionModeChoices.monthly,
    }

    def to_representation(self, value):
        return self.mapping[value]

    def to_internal_value(self, value):
        mapping = {v: k for k, v in self.mapping.items()}
        return mapping[value]


class FederatedDeadlineActivitySerializer(BaseFederatedActivitySerializer):
    id = FederatedIdField('json-ld:do-good-event')

    location = LocationSerializer(allow_null=True, required=False)

    start_time = DateField(source='start', allow_null=True)
    end_time = DateField(source='deadline', allow_null=True)
    application_deadline = DateField(source='registration_deadline', allow_null=True)

    event_attendance_mode = EventAttendanceModeField()
    join_mode = JoinModeField()
    duration = serializers.DurationField(allow_null=True)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = DeadlineActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'capacity',
            'location', 'start_time', 'end_time', 'application_deadline',
            'event_attendance_mode', 'duration', 'join_mode'
        )


class FederatedRegisteredDateActivitySerializer(BaseFederatedActivitySerializer):
    id = FederatedIdField('json-ld:do-good-event')

    location = LocationSerializer(allow_null=True, required=False)

    start_time = serializers.DateTimeField(source='start', allow_null=True)
    end_time = serializers.DateTimeField(source='end', allow_null=True, read_only=True)
    duration = serializers.DurationField(allow_null=True)

    event_attendance_mode = serializers.SerializerMethodField()
    join_mode = serializers.SerializerMethodField()

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = RegisteredDateActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'location', 'start_time', 'end_time',
            'duration', 'join_mode', 'event_attendance_mode'
        )

    def get_join_mode(self, obj):
        return JoinModeChoices.selected

    def get_event_attendance_mode(self, obj):
        return (
            EventAttendanceModeChoices.online if obj.location else EventAttendanceModeChoices.offline
        )


class SlotsSerializer(FederatedObjectSerializer):
    id = FederatedIdField('json-ld:sub-event')

    name = serializers.CharField(source='title', required=False, allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True, required=False)
    end_time = serializers.DateTimeField(source='end', read_only=True)
    location = LocationSerializer(allow_null=True, required=False)

    event_attendance_mode = EventAttendanceModeField(required=False, allow_null=True)

    duration = serializers.DurationField(required=False, allow_null=True)

    capacity = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.CharField(required=False, allow_null=True)
    location_hint = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    online_meeting_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    contributor_count = serializers.IntegerField(
        source='remote_contributor_count',
        required=False,
        allow_null=True,
    )

    def to_representation(self, instance):
        # Supplier platform should sent `contributor_count`
        # Consumer should store it in `remote_contributor_count`
        data = super().to_representation(instance)
        data['contributor_count'] = instance.contributor_count
        return data

    def create(self, validated_data):
        iri = validated_data.get('id')
        activity = validated_data.get('activity')
        sub_event = None
        location = validated_data.get('location')
        if isinstance(location, dict):
            validated_data['location'] = LocationSerializer(context=self.context).create(location)

        if iri:
            try:
                sub_event = SubEvent.objects.get(iri=iri)
            except SubEvent.DoesNotExist:
                sub_event = None

        existing_slot = None
        if activity:
            start = validated_data.get('start')
            duration = validated_data.get('duration')

            if sub_event:
                existing_slot = DateActivitySlot.objects.filter(
                    activity=activity,
                    origin=sub_event
                ).first()

                if existing_slot is None:
                    source_slot = getattr(sub_event, 'slot', None)
                    if source_slot is not None and source_slot.activity_id == activity.pk:
                        existing_slot = source_slot

            # Prefer matching an "orphan" slot by start/duration, so we link
            # origin instead of creating duplicates.
            if existing_slot is None and start is not None:
                qs = DateActivitySlot.objects.filter(
                    activity=activity,
                    start=start,
                )
                if sub_event is not None:
                    qs = qs.filter(origin__isnull=True) | DateActivitySlot.objects.filter(
                        activity=activity,
                        origin=sub_event,
                    )
                if duration is not None:
                    match = qs.filter(duration=duration).first()
                    if match is not None:
                        existing_slot = match
                if existing_slot is None:
                    existing_slot = qs.first()

            # Single-slot fallback (covers cases where SubEvent has no `iri` yet).
            #
            # Important: don't apply this when we have enough information to create
            # a distinct slot (e.g. a specific start/duration), otherwise syncing a
            # multi-slot event can incorrectly "reuse" the first created slot for
            # subsequent sub events.
            if (
                existing_slot is None
                and sub_event is None
                and start is None
                and duration is None
                and activity.slots.count() == 1
            ):
                existing_slot = activity.slots.first()

        if existing_slot is not None:
            if sub_event is not None and existing_slot.origin_id != sub_event.pk:
                validated_data['origin'] = sub_event
            return self.update(existing_slot, validated_data)

        validated_data.pop('id', None)
        if sub_event is not None:
            validated_data['origin'] = sub_event
        slot = DateActivitySlot(**validated_data)
        slot.save(run_triggers=False)
        return slot

    def update(self, instance, validated_data):
        validated_data.pop('id', None)
        location = validated_data.get('location')
        if isinstance(location, dict):
            validated_data['location'] = LocationSerializer(context=self.context).create(location)
        update_data = {}
        for key, value in validated_data.items():
            if key == 'location':
                update_data['location_id'] = value.pk if value else None
            elif key == 'activity':
                update_data['activity_id'] = value.pk if value else None
            elif key == 'origin':
                update_data['origin_id'] = value.pk if value else None
            else:
                update_data[key] = value
        if update_data:
            DateActivitySlot.objects.filter(pk=instance.pk).update(**update_data)
            instance.refresh_from_db()
        return instance

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = DateActivitySlot
        fields = FederatedObjectSerializer.Meta.fields + (
            'name', 'location', 'start_time', 'end_time',
            'event_attendance_mode', 'duration', 'capacity',
            'status', 'location_hint', 'online_meeting_url',
            'contributor_count',
        )


class FederatedSubEventSerializer(SlotsSerializer):
    pass


def _source_slot_for_sub_event(sub_event, source_date):
    if source_date is None:
        return None
    if sub_event.slot_id:
        slot = sub_event.slot
        if slot is not None and getattr(slot, 'activity_id', None) == source_date.pk:
            return slot
    return DateActivitySlot.objects.filter(activity=source_date, origin=sub_event).first()


def _is_online_from_sub_event(sub_event):
    if sub_event.event_attendance_mode == 'OnlineEventAttendanceMode':
        return True
    if sub_event.event_attendance_mode == 'OfflineEventAttendanceMode':
        return False
    return None


def _adopted_slot_has_active_participants(slot):
    return slot.participants.filter(
        status__in=['new', 'accepted', 'succeeded', 'scheduled', 'participating'],
    ).exists()


def sync_adopted_date_slots_from_source(event_do_good, source_date, adopted_date):
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
        src_slot = _source_slot_for_sub_event(sub, source_date)
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
            orphans = list(adopted_date.slots.filter(origin__isnull=True))
            if len(orphans) == 1:
                ad_slot = orphans[0]
        if ad_slot is not None and ad_slot.origin_id != sub.pk:
            ad_slot.origin = sub
            ad_slot.save(run_triggers=False, update_fields=['origin'])

        payload = {
            'name': src_slot.title if src_slot is not None else sub.name,
            'start_time': src_slot.start if src_slot is not None else sub.start_time,
            'duration': src_slot.duration if src_slot is not None else sub.duration,
            'capacity': src_slot.capacity if src_slot is not None else sub.capacity,
            'status': src_slot.status if src_slot is not None else None,
            'location_hint': src_slot.location_hint if src_slot is not None else None,
            'online_meeting_url': src_slot.online_meeting_url if src_slot is not None else None,
            'contributor_count': sub.contributor_count or 0,
        }
        if sub.iri:
            payload['id'] = sub.iri
        if src_slot is not None:
            payload['event_attendance_mode'] = (
                'OnlineEventAttendanceMode' if src_slot.is_online else 'OfflineEventAttendanceMode'
            )
            src_location = getattr(src_slot, 'location', None)
            location_ap_id = None
            if isinstance(src_location, dict):
                location_ap_id = src_location.get('id')
            else:
                location_ap_id = getattr(src_location, 'activity_pub_url', None)
            if location_ap_id:
                payload['location'] = {'id': location_ap_id}
        else:
            is_online = _is_online_from_sub_event(sub)
            if is_online is not None:
                payload['event_attendance_mode'] = (
                    'OnlineEventAttendanceMode' if is_online else 'OfflineEventAttendanceMode'
                )

        serializer = SlotsSerializer(instance=ad_slot, data=payload, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(activity=adopted_date)

    for orphan in adopted_date.slots.filter(origin__isnull=True):
        if _adopted_slot_has_active_participants(orphan):
            continue
        orphan.delete()


class FederatedDateActivitySerializer(BaseFederatedActivitySerializer):
    id = FederatedIdField('json-ld:do-good-event')

    sub_event = SlotsSerializer(many=True, source='slots')
    join_mode = JoinModeField()
    application_deadline = DateField(source='registration_deadline', allow_null=True)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = DateActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'capacity', 'sub_event', 'review', 'join_mode', 'application_deadline',
        )

    def create(self, validated_data):
        slots = validated_data.pop('slots', [])
        result = super().create(validated_data)

        field = self.fields['sub_event']
        for slot in slots:
            slot['activity'] = result

        validated_data[field.source] = field.create(slots)

        return result

    def update(self, instance, validated_data):
        slots = validated_data.pop('slots', [])
        result = super().update(instance, validated_data)

        field = self.fields['sub_event']
        for slot in slots:
            slot['activity'] = result

        validated_data[field.source] = field.update(instance.slots.all(), slots)

        return result


class FederatedPeriodicActivitySerializer(BaseFederatedActivitySerializer):
    id = FederatedIdField('json-ld:do-good-event')

    location = LocationSerializer(allow_null=True, required=False)
    image = ImageSerializer(required=False, allow_null=True)
    start_time = DateField(source='start', allow_null=True)
    end_time = DateField(source='deadline', allow_null=True, read_only=True)
    application_deadline = DateField(source='registration_deadline', allow_null=True)
    duration = serializers.DurationField(allow_null=True)
    repetition_mode = RepetitionModeField()
    event_attendance_mode = EventAttendanceModeField()
    join_mode = JoinModeField()
    slot_mode = serializers.SerializerMethodField()

    def get_slot_mode(self, obj):
        return SlotModeChoices.periodic

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = PeriodicActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'location', 'start_time', 'end_time', 'application_deadline',
            'duration', 'join_mode', 'event_attendance_mode',
            'repetition_mode', 'slot_mode'
        )


class FederatedScheduleActivitySerializer(BaseFederatedActivitySerializer):
    id = FederatedIdField('json-ld:do-good-event')

    location = LocationSerializer(allow_null=True, required=False)

    start_time = DateField(source='start', allow_null=True)
    end_time = DateField(source='deadline', allow_null=True)
    application_deadline = DateField(source='registration_deadline', allow_null=True)
    duration = serializers.DurationField(allow_null=True)

    event_attendance_mode = EventAttendanceModeField()
    join_mode = JoinModeField()
    slot_mode = serializers.SerializerMethodField()

    def get_slot_mode(self, obj):
        return SlotModeChoices.scheduled

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = ScheduleActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'location', 'start_time', 'end_time', 'application_deadline',
            'event_attendance_mode', 'duration', 'join_mode', 'slot_mode'
        )


class FederatedActivitySerializer(PolymorphicSerializer):
    resource_type_field_name = 'type'

    polymorphic_serializers = [
        FederatedDeadlineActivitySerializer,
        FederatedDeedSerializer,
        FederatedDateActivitySerializer,
        FederatedSubEventSerializer,
        FederatedFundingSerializer,
        FederatedGrantApplicationSerializer,
        FederatedCollectSerializer,
        FederatedRegisteredDateActivitySerializer,
        FederatedPeriodicActivitySerializer,
        FederatedScheduleActivitySerializer,
    ]

    model_type_mapping = {
        Deed: 'GoodDeed',
        Funding: 'CrowdFunding',
        GrantApplication: 'GrantApplication',
        DateActivity: 'DoGoodEvent',
        DateActivitySlot: 'Event',
        PeriodicActivity: 'DoGoodEvent',
        RegisteredDateActivity: 'DoGoodEvent',
        DeadlineActivity: 'DoGoodEvent',
        ScheduleActivity: 'DoGoodEvent',
        CollectActivity: 'CollectCampaign',

    }

    def __new__(cls, *args, **kwargs):
        cls.model_serializer_mapping = dict(
            (serializer.Meta.model, serializer) for serializer in cls.polymorphic_serializers
        )

        return super().__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.resource_type_model_mapping['DeadlineActivity'] = DeadlineActivity
        self.resource_type_model_mapping['DateActivity'] = DateActivity
        self.resource_type_model_mapping['DateActivitySlot'] = DateActivitySlot
        self.resource_type_model_mapping['RegisteredDateActivity'] = RegisteredDateActivity
        self.resource_type_model_mapping['PeriodicActivity'] = PeriodicActivity
        self.resource_type_model_mapping['ScheduleActivity'] = ScheduleActivity

    def to_resource_type(self, model_or_instance):
        if isinstance(model_or_instance, models.Model):
            model = type(model_or_instance)
        else:
            model = model_or_instance

        return self.model_type_mapping[model]

    def _get_resource_type_from_mapping(self, data):
        if data.get('type') == 'Event':
            return 'DateActivitySlot'
        if data.get('type') == 'DoGoodEvent':
            if data.get('slot_mode', 'SetSlotMode') == 'ScheduledSlotMode':
                return 'ScheduleActivity'
            elif data.get('slot_mode', 'SetSlotMode') == 'PeriodicSlotMode':
                return 'PeriodicActivity'
            elif data.get('join_mode', None) in ('selected', JoinModeChoices.selected):
                return 'RegisteredDateActivity'
            elif len(data.get('sub_event', [])) > 0:
                return 'DateActivity'
            else:
                return 'DeadlineActivity'

        return super()._get_resource_type_from_mapping(data)

    def save(self, *args, **kwargs):
        if not kwargs.get('owner'):
            kwargs['owner'] = self.context['request'].user

        return super().save(**kwargs)
