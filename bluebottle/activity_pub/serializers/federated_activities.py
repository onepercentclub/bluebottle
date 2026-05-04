import datetime
import logging
from io import BytesIO

import pytz
import requests
from django.contrib.gis.geos import Point
from django.core.files import File
from django.db import connection
from django.urls import reverse


from djmoney.money import Money
from rest_framework import exceptions
from rest_framework import serializers

from bluebottle.activity_pub.models import EventAttendanceModeChoices, Image as ActivityPubImage, JoinModeChoices, \
    SubEvent, RepetitionModeChoices, SlotModeChoices, Create
from bluebottle.activity_pub.serializers.base import FederatedObjectBaseSerializer
from bluebottle.activity_pub.serializers.fields import FederatedIdField, TypeField
from bluebottle.collect.models import CollectActivity, CollectType
from bluebottle.members.models import Member
from bluebottle.deeds.models import Deed
from bluebottle.files.models import Image
from bluebottle.files.serializers import ORIGINAL_SIZE
from bluebottle.funding.models import Funding
from bluebottle.grant_management.models import GrantApplication
from bluebottle.geo.models import Country, Geolocation
from bluebottle.organizations.models import Organization
from bluebottle.time_based.models import DateActivitySlot, DeadlineActivity, DateActivity, RegisteredDateActivity, \
    PeriodicActivity, ScheduleActivity
from bluebottle.utils.fields import RichTextField
from bluebottle.utils.models import get_default_language

logger = logging.getLogger(__name__)


class ImageSerializer(FederatedObjectBaseSerializer):
    id = FederatedIdField('json-ld:image')
    type = TypeField('Image')

    url = serializers.SerializerMethodField()
    name = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    type = TypeField('Image')

    def get_url(self, instance):
        return connection.tenant.build_absolute_url(
            reverse('activity-image', args=(instance.activity_set.first().pk, ORIGINAL_SIZE))
        )

    def create(self, validated_data):
        if not validated_data:
            return None

        image = ActivityPubImage.objects.from_iri(validated_data['id'])

        response = requests.get(image.url, timeout=30)
        response.raise_for_status()

        validated_data['file'] = File(BytesIO(response.content), name=validated_data['name'])

        return super().create(validated_data)

    class Meta:
        model = Image
        fields = FederatedObjectBaseSerializer.Meta.fields + (
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

        return {'url': connection.tenant.build_absolute_url(value.url)}


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


class AddressSerializer(FederatedObjectBaseSerializer):
    id = FederatedIdField('json-ld:address')
    type = TypeField('Address')

    street_address = serializers.CharField(source='street', required=False, allow_null=True)
    postal_code = serializers.CharField(required=False, allow_null=True)

    locality = serializers.CharField(required=False, allow_null=True)
    region = serializers.CharField(source='province', required=False, allow_null=True)
    country = CountryField(source='country.code', required=False, allow_null=True)

    class Meta:
        model = Geolocation
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'street_address', 'postal_code', 'locality',
            'region', 'country'
        )

    def to_internal_value(self, data):
        if not data:
            return {}
        result = super().to_internal_value(data)
        del result['id']
        return result


class MemberSerializer(FederatedObjectBaseSerializer):
    id = FederatedIdField('json-ld:person')
    type = TypeField('Person')
    name = serializers.CharField(source="full_name", allow_null=True, read_only=True)
    given_name = serializers.CharField(source="first_name", allow_null=True)
    family_name = serializers.CharField(source="last_name", allow_null=True)
    summary = serializers.CharField(
        source='description',
        allow_blank=True,
        allow_null=True,
        required=False
    )
    icon = ImageField(source='logo', required=False, allow_null=True)

    class Meta:
        model = Member
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'name', 'family_name', 'given_name', 'summary', 'icon'
        )


class OrganizationSerializer(FederatedObjectBaseSerializer):
    id = FederatedIdField('json-ld:organization')
    type = TypeField('Organization')
    name = serializers.CharField(allow_null=True)
    preferred_username = serializers.CharField(allow_null=True, source='slug')
    summary = serializers.CharField(
        source='description',
        allow_blank=True,
        allow_null=True,
        required=False
    )
    icon = ImageField(source='logo', required=False, allow_null=True)

    class Meta:
        model = Organization
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'name', 'summary', 'icon', 'preferred_username'
        )


class LocationSerializer(FederatedObjectBaseSerializer):
    id = FederatedIdField('json-ld:place')
    type = TypeField('Place')
    latitude = serializers.FloatField(source='position.x', allow_null=True)
    longitude = serializers.FloatField(source='position.y', allow_null=True)
    name = serializers.CharField(source='formatted_address', allow_null=True)

    address = AddressSerializer(source='*', allow_null=True)

    class Meta:
        model = Geolocation
        fields = FederatedObjectBaseSerializer.Meta.fields + ('latitude', 'longitude', 'name', 'address',)

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


class BaseFederatedActivitySerializer(FederatedObjectBaseSerializer):
    name = serializers.CharField(source='title')
    summary = RichTextField(source='description', allow_blank=True, allow_null=True)
    image = ImageSerializer(required=False, allow_null=True)
    organization = OrganizationSerializer(required=False, allow_null=True)
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return connection.tenant.build_absolute_url(
            obj.get_absolute_url()
        )

    def create(self, validated_data):
        source = Create.objects.get(object__iri=validated_data['id']).actor
        follow = source.follow_set.get()
        if follow.default_owner:
            validated_data['owner'] = follow.default_owner

        validated_data['host_organization'] = source.federated_object

        return super().create(validated_data)

    class Meta(FederatedObjectBaseSerializer.Meta):
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'name', 'summary', 'image', 'organization', 'url'
        )


class FederatedDeedSerializer(BaseFederatedActivitySerializer):
    id = FederatedIdField('json-ld:good-deed')
    type = TypeField('GoodDeed')

    start_time = DateField(source='start', allow_null=True)
    end_time = DateField(source='end', allow_null=True)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = Deed
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'start_time', 'end_time'
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
    type = TypeField('CollectCampaign')

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
    type = TypeField('CrowdFunding')

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
    type = TypeField('GrantApplication')

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
    type = TypeField('DoGoodEvent')

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
            'location', 'start_time', 'end_time', 'application_deadline',
            'event_attendance_mode', 'duration', 'join_mode'
        )


class FederatedRegisteredDateActivitySerializer(BaseFederatedActivitySerializer):
    id = FederatedIdField('json-ld:do-good-event')
    type = TypeField('DoGoodEvent')

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


class SlotsSerializer(FederatedObjectBaseSerializer):
    id = FederatedIdField('json-ld:sub-event')
    type = TypeField('subEvent')

    name = serializers.CharField(source='title', required=False, allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True, required=False)
    end_time = serializers.DateTimeField(source='end', read_only=True)
    location = LocationSerializer(allow_null=True, required=False)

    event_attendance_mode = EventAttendanceModeField()

    duration = serializers.DurationField(required=False, allow_null=True)

    def create(self, validated_data):

        iri = validated_data.get('id')
        if iri:
            try:
                sub_event = SubEvent.objects.get(iri=iri)
                activity = validated_data.get('activity')
                if activity:
                    existing_slot = DateActivitySlot.objects.filter(origin=sub_event, activity=activity).first()
                    if existing_slot:
                        for key, value in validated_data.items():
                            if key not in ('id', 'origin'):
                                setattr(existing_slot, key, value)
                        existing_slot.save()
                        return existing_slot
                validated_data.pop('id', None)
                validated_data['origin'] = sub_event
            except SubEvent.DoesNotExist:
                pass

        return super().create(validated_data)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = DateActivitySlot
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'name', 'location', 'start_time', 'end_time',
            'event_attendance_mode', 'duration',
        )


class FederatedDateActivitySerializer(BaseFederatedActivitySerializer):
    id = FederatedIdField('json-ld:do-good-event')
    type = TypeField('DoGoodEvent')

    sub_event = SlotsSerializer(many=True, source='slots')
    join_mode = JoinModeField()
    application_deadline = DateField(source='registration_deadline', allow_null=True)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = DateActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'sub_event', 'review', 'join_mode', 'application_deadline',
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
    type = TypeField('DoGoodEvent')

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
    type = TypeField('DoGoodEvent')

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
