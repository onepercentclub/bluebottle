import datetime
import logging
from io import BytesIO

import pytz
import requests
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.db import connection
from django.urls import reverse
from djmoney.money import Money
from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.relations import RelatedField

from bluebottle.activities.models import Contributor, RemoteMember
from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models import (
    EventAttendanceModeChoices, Image as ActivityPubImage, JoinModeChoices,
    ParticipationModeChoices, RepetitionModeChoices, SlotModeChoices, Create,
    ActivityPubModel, SubEvent, Team as ActivityPubTeam, Add, Follow,
)
from bluebottle.activity_pub.serializers.base import FederatedObjectBaseSerializer
from bluebottle.activity_pub.serializers.fields import FederatedIdField, TypeField
from bluebottle.activity_pub.utils import is_local
from bluebottle.collect.models import CollectActivity, CollectType, CollectContributor
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.files.models import Image
from bluebottle.files.serializers import ORIGINAL_SIZE
from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.funding.models import Funding
from bluebottle.geo.models import Country, Geolocation
from bluebottle.grant_management.models import GrantApplication
from bluebottle.members.models import Member
from bluebottle.organizations.models import Organization
from bluebottle.time_based.models import (
    DateActivitySlot, DateParticipant, DateRegistration, DeadlineActivity, DateActivity,
    DeadlineRegistration, PeriodicRegistration, PeriodicSlot, RegisteredDateActivity,
    PeriodicActivity, Registration, ScheduleActivity, ScheduleRegistration, ScheduleSlot,
    ScheduleParticipant, PeriodicParticipant, TeamScheduleRegistration, TeamScheduleSlot,
    TeamScheduleParticipant, Team as LocalTeam, TeamMember
)
from bluebottle.utils.fields import RichTextField
from bluebottle.utils.models import get_default_language

logger = logging.getLogger(__name__)


class ImageSerializer(FederatedObjectBaseSerializer):
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

        validated_data['file'] = File(BytesIO(response.content), name=validated_data['name'] or '')

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if self.instance.origin.iri != validated_data['id']:
            return self.create(validated_data)
        else:
            return super().update(instance, validated_data)

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

            return File(BytesIO(response.content), name=image.name or 'file')
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


class AddressIdField(FederatedIdField):
    def to_representation(self, value):
        if hasattr(value, 'origin') and value.origin:
            return value.origin.address.pub_url

        if hasattr(value, 'activity_pub_model') and value.activity_pub_model:
            return value.activity_pub_model.address.pub_url


class AddressSerializer(FederatedObjectBaseSerializer):
    id = AddressIdField()
    type = TypeField('Address')

    street_address = serializers.CharField(
        source='street', required=False, allow_null=True, allow_blank=True
    )
    postal_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    locality = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    region = serializers.CharField(
        source='province', required=False, allow_null=True, allow_blank=True
    )
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
    type = TypeField('Person')
    name = serializers.CharField(source="full_name", allow_null=True, read_only=True)
    given_name = serializers.CharField(source="first_name", allow_null=True)
    family_name = serializers.CharField(source="last_name", allow_null=True)
    email = serializers.CharField(allow_null=True)
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
            'name', 'family_name', 'given_name', 'email', 'summary', 'icon'
        )

    def save(self, *args, **kwargs):
        try:
            self.instance = RemoteMember.objects.get(origin__iri=self.validated_data['id'])
        except RemoteMember.DoesNotExist:
            pass

        return super().save(*args, **kwargs)

    def create(self, validated_data):
        result = RemoteMember.objects.create(
            **dict(
                (key, value) for key, value in validated_data.items() if
                key not in ['id', 'type']
            )
        )

        origin = ActivityPubModel.objects.from_iri(validated_data['id'])
        if origin:
            origin.adopted = result
            origin.save()

        return result


class OrganizationSerializer(FederatedObjectBaseSerializer):
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
    type = TypeField('Place')
    latitude = serializers.FloatField(source='position.x', allow_null=True)
    longitude = serializers.FloatField(source='position.y', allow_null=True)
    name = serializers.CharField(source='formatted_address', allow_null=True)

    address = AddressSerializer(source='*', allow_null=True)

    class Meta:
        model = Geolocation
        fields = FederatedObjectBaseSerializer.Meta.fields + ('latitude', 'longitude', 'name', 'address',)

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)

        try:
            internal_value['country'] = internal_value['country']['code']
        except KeyError:
            pass

        try:
            internal_value['position'] = Point(
                float(internal_value['position']['x']),
                float(internal_value['position']['y'])
            )
        except KeyError:
            pass

        return internal_value


class BaseFederatedActivitySerializer(FederatedObjectBaseSerializer):
    name = serializers.CharField(source='title')
    summary = RichTextField(source='description', allow_blank=True, allow_null=True)
    image = ImageSerializer(required=False, allow_null=True)
    organization = OrganizationSerializer(required=False, allow_null=True)
    url = serializers.SerializerMethodField()

    contributor_count = serializers.SerializerMethodField(required=False, allow_null=True)

    def get_contributor_count(self, obj):
        return obj.active_contributors.count()

    def get_url(self, obj):
        return connection.tenant.build_absolute_url(
            obj.get_absolute_url()
        )

    def create(self, validated_data):
        source = Create.objects.get(object__iri=validated_data['id']).actor
        follow = source.follow_set.get()
        if follow.default_owner and not validated_data.get('owner'):
            validated_data['owner'] = follow.default_owner

        validated_data['host_organization'] = source.adopted

        return super().create(validated_data)

    class Meta(FederatedObjectBaseSerializer.Meta):
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'name', 'summary', 'image', 'organization', 'contributor_count', 'url'
        )


class FederatedDeedSerializer(BaseFederatedActivitySerializer):
    type = TypeField('GoodDeed')

    start_time = DateField(source='start', allow_null=True)
    end_time = DateField(source='end', allow_null=True)

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
    type = TypeField('CrowdFunding')

    location = LocationSerializer(source='impact_location', allow_null=True, required=False)

    end_time = serializers.DateTimeField(source='deadline')
    target = serializers.DecimalField(source='target.amount', decimal_places=2, max_digits=10)
    target_currency = serializers.CharField(source='target.currency')
    donated = serializers.DecimalField(source='amount_raised.amount', decimal_places=2, max_digits=10)
    donated_currency = serializers.CharField(source='amount_raised.currency')

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = Funding
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'location', 'end_time',
            'target', 'target_currency',
            'donated', 'donated_currency'
        )

    def to_internal_value(self, validated_data):
        internal_value = super().to_internal_value(validated_data)
        if internal_value.get('target'):
            internal_value['target'] = Money(
                **internal_value['target']
            )
        if internal_value.get('amount_raised'):
            donated = internal_value.pop('amount_raised')
            internal_value['amount_donated'] = Money(
                **donated
            )

        return internal_value


class FederatedGrantApplicationSerializer(BaseFederatedActivitySerializer):
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


class ParticipationModeField(serializers.Field):
    def __init__(self, *args, **kwargs):
        kwargs['source'] = kwargs.get('source', 'team_activity')
        kwargs['required'] = False
        kwargs['allow_null'] = True
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        if value == 'teams':
            return ParticipationModeChoices.teams
        return ParticipationModeChoices.individuals

    def to_internal_value(self, value):
        if value == ParticipationModeChoices.teams:
            return 'teams'
        return 'individuals'


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
            'capacity',
            'location', 'start_time', 'end_time', 'application_deadline',
            'event_attendance_mode', 'duration', 'join_mode'
        )


class FederatedRegisteredDateActivitySerializer(BaseFederatedActivitySerializer):
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


class RelatedParentField(RelatedField):
    def get_queryset(self):
        # TODO: filter queryset on correct types
        return DateActivity.objects.all()

    def to_representation(self, value):
        if hasattr(value, 'activity_pub_model'):
            return value.activity_pub_model.pub_url

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = {'id': data}

        activity_pub_model = ActivityPubModel.objects.from_iri(data['id'])
        if activity_pub_model.is_local:
            return activity_pub_model.origin
        else:
            return activity_pub_model.adopted


class DateSlotsSerializer(FederatedObjectBaseSerializer):
    type = TypeField('subEvent')

    name = serializers.CharField(source='title', required=False, allow_null=True, allow_blank=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True, required=False)
    end_time = serializers.DateTimeField(source='end', read_only=True)
    location = LocationSerializer(allow_null=True, required=False)

    event_attendance_mode = EventAttendanceModeField(required=False, allow_null=True)

    duration = serializers.DurationField(required=False, allow_null=True)

    capacity = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.CharField(required=False, allow_null=True)
    location_hint = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    online_meeting_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    parent = RelatedParentField(source='activity')

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

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = DateActivitySlot
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'name', 'location', 'start_time', 'end_time',
            'event_attendance_mode', 'duration', 'capacity',
            'status', 'location_hint', 'online_meeting_url',
            'parent', 'contributor_count',
        )


class ScheduleSlotsSerializer(FederatedObjectBaseSerializer):
    type = TypeField('subEvent')

    start_time = serializers.DateTimeField(source='start', allow_null=True, required=False)
    end_time = serializers.DateTimeField(source='end', read_only=True)
    location = LocationSerializer(allow_null=True, required=False)

    event_attendance_mode = EventAttendanceModeField(required=False, allow_null=True)

    duration = serializers.DurationField(required=False, allow_null=True)

    status = serializers.CharField(required=False, allow_null=True)
    location_hint = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    online_meeting_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    parent = RelatedParentField(source='activity')

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = ScheduleSlot
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'location', 'start_time', 'end_time',
            'event_attendance_mode', 'duration',
            'status', 'location_hint', 'online_meeting_url',
            'parent',
        )


class PeriodicSlotsSerializer(FederatedObjectBaseSerializer):
    type = TypeField('subEvent')

    start_time = serializers.DateTimeField(source='start', allow_null=True, required=False)
    end_time = serializers.DateTimeField(source='end', read_only=True)

    duration = serializers.DurationField(required=False, allow_null=True)

    status = serializers.CharField(required=False, allow_null=True)

    parent = RelatedParentField(source='activity')

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = PeriodicSlot
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'start_time',
            'end_time',
            'duration',
            'status',
            'parent',
        )


class FederatedDateActivitySerializer(BaseFederatedActivitySerializer):
    type = TypeField('DoGoodEvent')

    sub_event = DateSlotsSerializer(many=True, source='slots')
    join_mode = JoinModeField()
    application_deadline = DateField(source='registration_deadline', allow_null=True)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = DateActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'capacity', 'sub_event', 'review', 'join_mode', 'application_deadline',
        )

    def get_contributor_count(self, obj):
        return obj.participants.filter(status__in=['accepted', 'new', 'succeeded']).count()

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
        validated_data['slots'] = []
        for index, slot in enumerate(slots):
            slot['activity'] = result
            field.child.initial_data = self.initial_data['sub_event'][index]
            validated_data['slots'].append(
                field.child.update(
                    SubEvent.objects.from_iri(slot.pop('id')).adopted,
                    slot
                )
            )

        return result


class FederatedPeriodicActivitySerializer(BaseFederatedActivitySerializer):
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

    def get_contributor_count(self, obj):
        return obj.registrations.filter(status__in=['new', 'accepted']).count()

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = PeriodicActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'location', 'start_time', 'end_time', 'application_deadline',
            'duration', 'join_mode', 'event_attendance_mode',
            'repetition_mode', 'slot_mode'
        )


class FederatedScheduleActivitySerializer(BaseFederatedActivitySerializer):
    type = TypeField('DoGoodEvent')

    location = LocationSerializer(allow_null=True, required=False)

    start_time = DateField(source='start', allow_null=True)
    end_time = DateField(source='deadline', allow_null=True)
    application_deadline = DateField(source='registration_deadline', allow_null=True)
    duration = serializers.DurationField(allow_null=True)

    event_attendance_mode = EventAttendanceModeField()
    join_mode = JoinModeField()
    participation_mode = ParticipationModeField()
    slot_mode = serializers.SerializerMethodField()

    def get_slot_mode(self, obj):
        return SlotModeChoices.scheduled

    def get_contributor_count(self, obj):
        if obj.team_activity == 'teams':
            return obj.registrations.filter(status__in=['new', 'accepted']).count()
        return obj.active_participants.count()

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = ScheduleActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'location', 'start_time', 'end_time', 'application_deadline',
            'event_attendance_mode', 'duration', 'join_mode', 'participation_mode',
            'slot_mode'
        )


class RelatedActivityField(RelatedField):
    def get_queryset(self):
        # TODO: filter queryset on correct types
        return ActivityPubModel.objects.all()

    def get_origin_value(self, instance):
        if getattr(instance, 'slot', None):
            return instance.slot
        return getattr(instance, self.source)

    def to_representation(self, value):
        if hasattr(self.parent.instance, 'slot') and self.parent.instance.slot:
            value = self.parent.instance.slot

        if hasattr(value, 'activity_pub_model'):
            return value.activity_pub_model.pub_url
        elif hasattr(value, 'origin'):
            return value.origin.pub_url

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = {'id': data}

        activity_pub_model = ActivityPubModel.objects.from_iri(data['id'])
        if activity_pub_model.is_local:
            return activity_pub_model.origin
        else:
            return adapter.adopt(activity_pub_model)


class RegistrationSerializer(FederatedObjectBaseSerializer):
    type = TypeField('Join')
    actor = MemberSerializer(source='user')
    object = RelatedActivityField(source='activity')
    motivation = serializers.CharField(source='answer')

    class Meta:
        model = Registration
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'actor', 'object', 'motivation'
        )


class MotivationField(serializers.CharField):
    def to_representation(self, value):
        if hasattr(value, 'registration'):
            value = value.registration

        if isinstance(value, Registration):
            return value.answer

    def to_internal_value(self, data):
        return {'answer': data}


class ContributorSerializer(FederatedObjectBaseSerializer):
    type = TypeField('Join')
    actor = MemberSerializer(source='user')
    object = RelatedActivityField(source='activity')
    motivation = MotivationField(required=False, allow_null=True, source='*')

    class Meta:
        model = Contributor
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'actor', 'object', 'motivation'
        )

    def get_polymorphic_serializer(self, validated_data):
        activity = validated_data['activity']
        model_name = activity._meta.model_name

        if (
            model_name == 'scheduleactivity'
            and getattr(activity, 'team_activity', None) == 'teams'
        ):
            return TeamScheduleRegistrationSerializer()

        serializer_mapping = {
            'deed': DeedParticipantSerializer,
            'collectactivity': CollectParticipantSerializer,
            'deadlineactivity': DeadlineParticipantSerializer,
            'scheduleactivity': ScheduleRegistrationSerializer,
            'periodicactivity': PeriodicRegistrationSerializer,
            'dateactivityslot': DateParticipantSerializer,
            'dateactivity': DateRegistrationSerializer,
            'scheduleslot': ScheduleParticipantSerializer,
            'periodicslot': PeriodicParticipantSerializer,
            'teamscheduleslot': TeamScheduleParticipantSerializer,
        }

        return serializer_mapping[model_name]()

    def create(self, validated_data):
        validated_data.pop('id')
        user = validated_data.pop('user')

        field = self.fields['actor']
        field.initial_data = self.initial_data['actor']
        field.is_valid(raise_exception=True)
        if is_local(user['id']):
            validated_data['user'] = ActivityPubModel.objects.from_iri(user['id']).origin
        else:
            validated_data['remote_user'] = field.save()

        polymorphic_serializer = self.get_polymorphic_serializer(validated_data)
        if isinstance(polymorphic_serializer, TeamScheduleRegistrationSerializer):
            return polymorphic_serializer.create(
                validated_data,
                instrument=self.initial_data.get('instrument'),
            )
        return polymorphic_serializer.create(validated_data)


class BaseContributorSerializer(FederatedObjectBaseSerializer):
    def get_contributor(self, validated_data):
        return self.model.objects.filter(
            activity=validated_data['activity'],
            remote_user=validated_data['remote_user'],
        ).first()

    def update(self, contributor, validated_data):
        contributor.states.reapply(save=True)

    def create(self, validated_data):
        contributor = self.get_contributor(validated_data)
        if contributor:
            self.update(contributor, validated_data)
            return contributor
        else:
            return self.model.objects.create(**validated_data)


class DeedParticipantSerializer(BaseContributorSerializer):
    model = DeedParticipant

    def create(self, validated_data):
        validated_data.pop('answer')
        return super().create(validated_data)


class CollectParticipantSerializer(BaseContributorSerializer):
    model = CollectContributor

    def create(self, validated_data):
        validated_data.pop('answer')
        return super().create(validated_data)


class DeadlineParticipantSerializer(BaseContributorSerializer):
    model = DeadlineRegistration

    def get_contributor(self, validated_data):
        contributor = super().get_contributor(validated_data)
        if contributor:
            return contributor.participants.first()


class ScheduleRegistrationSerializer(BaseContributorSerializer):
    model = ScheduleRegistration

    def get_contributor(self, validated_data):
        contributor = super().get_contributor(validated_data)
        if contributor:
            return contributor.participants.first()


class ScheduleParticipantSerializer(BaseContributorSerializer):
    model = ScheduleParticipant

    def get_contributor(self, validated_data):
        return self.model.objects.filter(
            activity=validated_data['activity'],
            user=validated_data['user'],
        ).first()

    def update(self, contributor, validated_data):
        contributor.slot = validated_data['slot']
        contributor.save()

    def create(self, validated_data):
        slot = validated_data.pop('activity')

        validated_data['registration'] = ScheduleRegistration.objects.get(
            activity=slot.activity,
            user=validated_data['user']
        )

        validated_data['slot'] = slot
        validated_data['activity'] = slot.activity

        validated_data.pop('answer')

        return super().create(validated_data)


class PeriodicParticipantSerializer(BaseContributorSerializer):
    model = PeriodicParticipant

    def get_contributor(self, validated_data):
        return self.model.objects.filter(
            activity=validated_data['activity'],
            user=validated_data['user'],
        ).first()

    def update(self, contributor, validated_data):
        contributor.slot = validated_data['slot']
        contributor.save()

    def create(self, validated_data):
        slot = validated_data.pop('activity')

        validated_data['registration'] = PeriodicRegistration.objects.get(
            activity=slot.activity,
            user=validated_data['user']
        )

        validated_data['slot'] = slot
        validated_data['activity'] = slot.activity

        validated_data.pop('answer')

        return super().create(validated_data)


class PeriodicRegistrationSerializer(BaseContributorSerializer):
    model = PeriodicRegistration

    def update(self, contributor, validated_data):
        contributor.states.start(save=True)


class DateRegistrationSerializer(BaseContributorSerializer):
    model = DateRegistration


class DateParticipantSerializer(BaseContributorSerializer):
    model = DateParticipant

    def create(self, validated_data):
        slot = validated_data.pop('activity')

        validated_data['registration'] = DateRegistration.objects.get(
            activity=slot.activity,
            remote_user=validated_data['remote_user']
        )

        validated_data['slot'] = slot
        validated_data['activity'] = slot.activity

        validated_data.pop('answer')

        return super().create(validated_data)


class FederatedTeamSerializer(FederatedObjectBaseSerializer):
    type = TypeField('Team')
    name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    summary = serializers.CharField(
        source='description', required=False, allow_null=True, allow_blank=True
    )
    attributed_to = RelatedActivityField(source='activity')
    captain = MemberSerializer(source='user', required=False, allow_null=True)

    class Meta:
        model = LocalTeam
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'name', 'summary', 'attributed_to', 'captain',
        )

    def create(self, validated_data):
        validated_data.pop('id', None)
        captain = validated_data.pop('user', None)
        activity = validated_data['activity']

        remote_user = None
        user = None
        if captain:
            field = self.fields['captain']
            if self.initial_data.get('captain'):
                field.initial_data = self.initial_data['captain']
                field.is_valid(raise_exception=True)
                captain_id = (
                    captain['id'] if isinstance(captain, dict) else captain
                )
                if is_local(captain_id):
                    user = ActivityPubModel.objects.from_iri(captain_id).origin
                else:
                    remote_user = field.save()

        team = LocalTeam.objects.create(
            activity=activity,
            user=user,
            remote_user=remote_user,
            name=validated_data.get('name'),
            description=validated_data.get('description'),
            registration=validated_data.get('registration'),
        )
        return team


class TeamInstrumentField(serializers.Field):
    """Outbound nested Team for a team-schedule Join."""

    def get_attribute(self, instance):
        return instance.teams.first()

    def get_origin_value(self, instance):
        return instance.teams.first()

    def to_representation(self, team):
        if team is None:
            return None
        return FederatedTeamSerializer(instance=team).data

    def to_internal_value(self, data):
        return data


class TeamScheduleRegistrationSerializer(BaseContributorSerializer):
    model = TeamScheduleRegistration

    def create(self, validated_data, instrument=None):
        answer = validated_data.pop('answer', None)
        remote_user = validated_data.get('remote_user')
        user = validated_data.get('user')
        activity = validated_data['activity']

        existing = TeamScheduleRegistration.objects.filter(
            activity=activity,
            remote_user=remote_user,
            user=user,
        ).first()
        if existing:
            team = existing.teams.first()
            try:
                if team and team.status == 'withdrawn':
                    team.states.rejoin(save=True)
                elif existing.status == 'withdrawn':
                    existing.states.restore(save=True)
            except TransitionNotPossible:
                pass
            return existing

        registration = TeamScheduleRegistration(
            activity=activity,
            user=user,
            remote_user=remote_user,
            answer=answer,
        )
        registration.execute_triggers()
        registration.save()

        team_name = None
        team_description = None
        instrument_iri = None
        if isinstance(instrument, dict):
            team_name = instrument.get('name')
            team_description = instrument.get('summary')
            instrument_iri = instrument.get('id') or instrument.get('iri')
        elif isinstance(instrument, str):
            instrument_iri = instrument

        team = LocalTeam(
            activity=activity,
            registration=registration,
            user=user,
            remote_user=remote_user,
            name=team_name,
            description=team_description,
        )
        team.execute_triggers()
        team.save()

        if instrument_iri:
            ap_team = ActivityPubModel.objects.from_iri(instrument_iri)
            if ap_team and not ap_team.adopted:
                ap_team.adopted = team
                if (
                    isinstance(ap_team, ActivityPubTeam) and
                    not ap_team.attributed_to_id and
                    hasattr(activity, 'activity_pub_model')
                ):
                    ap_team.attributed_to = activity.activity_pub_model
                ap_team.save()

        return registration


class TeamScheduleRegistrationJoinSerializer(FederatedObjectBaseSerializer):
    """Outbound Join representation for a team schedule registration."""
    type = TypeField('Join')
    actor = MemberSerializer(source='user')
    object = RelatedActivityField(source='activity')
    motivation = serializers.CharField(
        source='answer', required=False, allow_null=True, allow_blank=True
    )
    instrument = TeamInstrumentField(required=False, allow_null=True)

    class Meta:
        model = TeamScheduleRegistration
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'actor', 'object', 'motivation', 'instrument',
        )

    def create(self, validated_data):
        raise NotImplementedError('Use ContributorSerializer for adopting Joins')


class TeamScheduleParticipantSerializer(BaseContributorSerializer):
    model = TeamScheduleParticipant

    def get_contributor(self, validated_data):
        filters = {
            'activity': validated_data['activity'],
        }
        if validated_data.get('remote_user'):
            filters['remote_user'] = validated_data['remote_user']
        elif validated_data.get('user'):
            filters['user'] = validated_data['user']
        else:
            return None
        return self.model.objects.filter(**filters).first()

    def update(self, contributor, validated_data):
        if validated_data.get('slot'):
            contributor.slot = validated_data['slot']
            contributor.save()

    def create(self, validated_data):
        slot = validated_data.pop('activity')
        filters = {'activity': slot.activity}
        if validated_data.get('remote_user'):
            filters['remote_user'] = validated_data['remote_user']
        elif validated_data.get('user'):
            filters['user'] = validated_data['user']
        else:
            raise serializers.ValidationError(
                'Team schedule participant requires a user or remote_user identity'
            )

        registration = TeamScheduleRegistration.objects.filter(**filters).first()
        if registration is None:
            raise serializers.ValidationError(
                'No matching TeamScheduleRegistration found for this participant'
            )

        team = registration.teams.first()
        if team is None:
            raise serializers.ValidationError(
                'Matching TeamScheduleRegistration has no team'
            )

        member_filters = {
            key: value for key, value in filters.items() if key != 'activity'
        }
        team_member = team.team_members.filter(**member_filters).first()

        # Keep participants on the team's canonical slot (UI uses slots[0]).
        if team_member:
            preferred = team_member.team.slots.order_by('pk').first()
            if preferred:
                slot = preferred

        validated_data['registration'] = registration
        validated_data['slot'] = slot
        validated_data['activity'] = slot.activity
        validated_data['team_member'] = team_member
        validated_data.pop('answer', None)

        return super().create(validated_data)


class TeamMemberAddSerializer(FederatedObjectBaseSerializer):
    type = TypeField('Add')
    actor = MemberSerializer(source='user')
    object = MemberSerializer(source='user')
    target = serializers.SerializerMethodField()

    class Meta:
        model = TeamMember
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'actor', 'object', 'target',
        )

    def get_target(self, obj):
        if hasattr(obj.team, 'activity_pub_model'):
            return obj.team.activity_pub_model.pub_url
        if hasattr(obj.team, 'origin'):
            return obj.team.origin.pub_url

    def to_representation(self, instance):
        data = super().to_representation(instance)
        target = self.get_target(instance)
        if target:
            data['target'] = target
        return data

    @staticmethod
    def _resource_iri(value):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return value.get('id') or value.get('iri')
        return None

    def _get_add_platform(self):
        request = self.context.get('request') if self.context else None
        if request is not None and getattr(request, 'auth', None):
            return request.auth

        add_iri = self._resource_iri(self.initial_data.get('id'))
        if not add_iri:
            return None

        add = ActivityPubModel.objects.from_iri(add_iri)
        if isinstance(add, Add) and add.platform_id:
            return add.platform
        return None

    def _event_for_team(self, ap_team, team):
        if isinstance(ap_team, ActivityPubTeam) and ap_team.attributed_to_id:
            return ap_team.attributed_to
        return getattr(team.activity, 'activity_pub_model', None)

    def _platform_may_modify_event(self, platform, event):
        if Create.objects.filter(object=event, recipients__actor=platform).exists():
            return True

        for create in event.create_set.all():
            if Follow.objects.filter(actor=platform, object=create.actor).exists():
                return True
        return False

    def _validate_add(self, actor_iri, object_iri, ap_team, team):
        if not actor_iri or actor_iri != object_iri:
            raise serializers.ValidationError({
                'object': 'Add object must match actor',
            })

        if ap_team is None:
            raise serializers.ValidationError({
                'target': 'Add target team is required',
            })

        event = self._event_for_team(ap_team, team)
        if event is None:
            raise serializers.ValidationError({
                'target': 'Add target team is not attributed to an activity',
            })

        event_activity = event.origin if event.is_local else event.adopted
        if event_activity is None or event_activity.pk != team.activity_id:
            raise serializers.ValidationError({
                'target': 'Add target team does not belong to the attributed activity',
            })

        platform = self._get_add_platform()
        if platform is None:
            raise serializers.ValidationError(
                'Add platform could not be determined'
            )

        if not self._platform_may_modify_event(platform, event):
            raise serializers.ValidationError({
                'target': 'Platform is not authorized to add members to this team',
            })

        return platform

    def create(self, validated_data):
        validated_data.pop('id', None)
        actor_data = self.initial_data.get('actor')
        object_data = self.initial_data.get('object')
        actor_iri = self._resource_iri(actor_data)
        object_iri = self._resource_iri(object_data)
        user_data = object_data or actor_data

        target = self.initial_data.get('target')
        if isinstance(target, str):
            target = {'id': target}
        elif isinstance(target, dict) and 'id' not in target and 'iri' in target:
            target = {'id': target['iri']}

        target_iri = self._resource_iri(target)
        if not target_iri:
            raise serializers.ValidationError({
                'target': 'Add target team is required',
            })

        ap_team = ActivityPubModel.objects.from_iri(target_iri)
        if ap_team is None:
            raise serializers.ValidationError({
                'target': 'Unknown Add target team',
            })

        if ap_team.is_local:
            team = ap_team.origin
        elif ap_team.adopted:
            team = ap_team.adopted
        else:
            team = adapter.adopt(ap_team)

        if team is None:
            raise serializers.ValidationError({
                'target': 'Add target team could not be resolved',
            })

        platform = self._validate_add(actor_iri, object_iri, ap_team, team)

        field = self.fields['object']
        field.initial_data = user_data
        field.is_valid(raise_exception=True)
        person_id = user_data['id'] if isinstance(user_data, dict) else user_data

        if is_local(person_id):
            raise serializers.ValidationError({
                'object': 'Cannot add a local person via remote Add',
            })

        remote_user = field.save()
        person = getattr(remote_user, 'origin', None)
        if (
            person is not None and
            person.source_id and
            person.source_id != platform.id
        ):
            raise serializers.ValidationError({
                'object': 'Person does not belong to the sending platform',
            })

        existing = TeamMember.objects.filter(
            team=team, user=None, remote_user=remote_user
        ).first()
        if existing:
            try:
                if existing.status == 'withdrawn':
                    existing.states.reapply(save=True)
                elif existing.status == 'removed':
                    existing.states.readd(save=True)
                elif existing.status == 'rejected':
                    existing.states.accept(save=True)
            except TransitionNotPossible:
                pass
            return existing

        member = TeamMember(
            team=team,
            user=None,
            remote_user=remote_user,
        )
        member.execute_triggers()
        member.save()
        return member


class RelatedTeamSlotField(RelatedField):
    def get_queryset(self):
        return ActivityPubModel.objects.all()

    def get_origin_value(self, instance):
        return getattr(instance, 'team', None)

    def to_representation(self, value):
        if value is None:
            return None
        # Prefer the federated identity shared across platforms (adopted-from Team).
        try:
            if value.origin:
                return value.origin.pub_url
        except (AttributeError, ObjectDoesNotExist):
            pass
        if hasattr(value, 'activity_pub_model'):
            return value.activity_pub_model.pub_url

    def to_internal_value(self, data):
        if data is None:
            raise serializers.ValidationError('Team is required for team schedule slots')
        if isinstance(data, str):
            data = {'id': data}
        team_iri = data.get('id') or data.get('iri')
        if not team_iri:
            raise serializers.ValidationError('Team is required for team schedule slots')

        ap_team = ActivityPubModel.objects.from_iri(team_iri)
        if not ap_team:
            raise serializers.ValidationError('Unknown team')
        if ap_team.is_local:
            team = ap_team.origin
        elif ap_team.adopted:
            team = ap_team.adopted
        else:
            team = adapter.adopt(ap_team)

        if team is None:
            raise serializers.ValidationError('Team could not be resolved')
        return team


class TeamScheduleSlotsSerializer(ScheduleSlotsSerializer):
    type = TypeField('subEvent')
    team = RelatedTeamSlotField()

    class Meta(ScheduleSlotsSerializer.Meta):
        model = TeamScheduleSlot
        fields = ScheduleSlotsSerializer.Meta.fields + ('team',)

    def _prepare_slot_validated_data(self, validated_data):
        """
        Drop inbound status (let ModelChangedTriggers run schedule) and hydrate
        nested federated objects such as location.
        """
        validated_data.pop('status', None)

        for field in self.fields.values():
            if isinstance(field, FederatedObjectBaseSerializer):
                if (
                    field.source != '*' and
                    field.source in validated_data and
                    validated_data[field.source]
                ):
                    field_data = validated_data[field.source]
                    if isinstance(field_data, dict) and field_data.get('id'):
                        if is_local(field_data['id']):
                            validated_data[field.source] = ActivityPubModel.objects.from_iri(
                                field_data['id']
                            ).origin
                        else:
                            field.initial_data = field_data
                            validated_data[field.source] = field.create(field_data)

        return validated_data

    def _team_slot_to_reuse(self, validated_data, instance=None):
        """
        Always prefer the team's original blank slot from CreateTeamSlotEffect.
        The UI shows team.slots[0]; creating a second scheduled slot leaves that
        blank while RelatedTransitionEffect still schedules the team.
        """
        team = validated_data.get('team') or getattr(instance, 'team', None)
        if not team:
            raise serializers.ValidationError({
                'team': 'Team is required to adopt a team schedule slot',
            })

        validated_data['team'] = team
        existing = team.slots.order_by('pk').first()
        if existing:
            return existing

        return instance

    def _link_adopted(self, iri, result):
        origin = ActivityPubModel.objects.from_iri(iri) if iri else None
        if origin and hasattr(origin, 'adopted'):
            origin.adopted = result
            origin.save()

    def create(self, validated_data):
        iri = validated_data.pop('id', None)
        validated_data = self._prepare_slot_validated_data(validated_data)
        existing = self._team_slot_to_reuse(validated_data)

        if existing:
            result = serializers.ModelSerializer.update(self, existing, validated_data)
        else:
            result = serializers.ModelSerializer.create(self, validated_data)

        self._link_adopted(iri, result)
        return result

    def update(self, instance, validated_data):
        iri = validated_data.pop('id', None)
        validated_data = self._prepare_slot_validated_data(validated_data)
        target = self._team_slot_to_reuse(validated_data, instance=instance) or instance
        result = serializers.ModelSerializer.update(self, target, validated_data)
        self._link_adopted(iri, result)
        return result
