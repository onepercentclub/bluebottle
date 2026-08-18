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
from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.fields import SkipField
from rest_framework.relations import RelatedField

from bluebottle.activities.models import Contributor, RemoteMember
from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models import (
    EventAttendanceModeChoices, Image as ActivityPubImage, JoinModeChoices,
    ParticipationModeChoices, RepetitionModeChoices, SlotModeChoices, Create,
    ActivityPubModel, SubEvent, Team as ActivityPubTeam,
)
from bluebottle.activity_pub.serializers.base import FederatedObjectBaseSerializer
from bluebottle.activity_pub.serializers.fields import FederatedIdField, MoneyField, TypeField
from bluebottle.activity_pub.utils import (
    is_local, resource_iri, event_for_team, platform_may_modify_event,
    sending_platform,
)
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

    lookup_field = 'origin__iri'
    lookup_url_kwarg = 'id'

    def get_queryset(self):
        return RemoteMember.objects.all()


class FederatedMemberSerializer(MemberSerializer):
    def get_origin_value(self, instance):
        return instance.user

    def to_representation(self, instance):
        user = getattr(instance, 'user', None)
        if user is None:
            return None
        return super().to_representation(user)

    def validate_empty_values(self, data):
        is_empty, value = super().validate_empty_values(data)
        if is_empty and not value:
            return True, {}
        return is_empty, value

    def to_internal_value(self, data):
        result = super().to_internal_value(data)
        iri = result.get('id')
        if iri and is_local(iri):
            return {'user': ActivityPubModel.objects.from_iri(iri).origin}

        self._validated_data = result
        self._errors = {}
        return {'remote_user': self.save()}


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
    video_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)

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
            'name', 'summary', 'image', 'organization', 'contributor_count', 'url', 'video_url'
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
    def to_representation(self, value):
        return value.safe_translation_getter(
            'name',
            language_code=get_default_language(),
            any_language=True,
        )

    def to_internal_value(self, data):
        if not data:
            return None

        lang = get_default_language()
        collect_type = self.get_queryset().translated(lang, name=data).first()
        if collect_type:
            return collect_type
        return self.get_queryset().model.objects.language(lang).create(name=data)


class FederatedCollectSerializer(BaseFederatedActivitySerializer):
    type = TypeField('CollectCampaign')

    start_time = DateField(source='start', allow_null=True)
    end_time = DateField(source='end', allow_null=True)
    collect_type = ParlerNameRelatedField(
        queryset=CollectType.objects.all(),
        allow_null=True,
        required=False,
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
    target = MoneyField()
    target_currency = serializers.CharField(source='target.currency', read_only=True)
    donated = MoneyField(source='amount_raised')
    donated_currency = serializers.CharField(source='amount_raised.currency', read_only=True)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = Funding
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'location', 'end_time',
            'target', 'target_currency',
            'donated', 'donated_currency'
        )

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)
        amount_raised = internal_value.pop('amount_raised', None)
        if amount_raised is not None:
            internal_value['amount_donated'] = amount_raised
        return internal_value


class FederatedGrantApplicationSerializer(BaseFederatedActivitySerializer):
    type = TypeField('GrantApplication')

    location = LocationSerializer(source='impact_location', allow_null=True, required=False)

    start_time = serializers.DateTimeField(source='started', required=False, allow_null=True)
    target = MoneyField(required=False, allow_null=True)
    target_currency = serializers.CharField(source='target.currency', read_only=True)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = GrantApplication
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'location', 'start_time',
            'target', 'target_currency',
        )


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

    sub_event = DateSlotsSerializer(many=True, source='publishable_slots')
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
        slots = validated_data.pop('publishable_slots', None)
        if slots is None:
            slots = validated_data.pop('slots', [])
        result = super().create(validated_data)

        field = self.fields['sub_event']
        for slot in slots:
            slot['activity'] = result

        validated_data[field.source] = field.create(slots)

        return result

    def update(self, instance, validated_data):
        slots = validated_data.pop('publishable_slots', validated_data.pop('slots', []))
        result = super().update(instance, validated_data)

        field = self.fields['sub_event']
        validated_data['publishable_slots'] = []
        for index, slot in enumerate(slots):
            slot['activity'] = result
            field.child.initial_data = self.initial_data['sub_event'][index]
            validated_data['publishable_slots'].append(
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

    def get_attribute(self, instance):
        if getattr(instance, 'slot', None):
            return instance.slot
        if self.source == '*':
            return getattr(instance, 'activity', instance)
        return super().get_attribute(instance)

    def get_origin_value(self, instance):
        if getattr(instance, 'slot', None):
            return instance.slot
        return getattr(instance, 'activity', None)

    def to_representation(self, value):
        if hasattr(value, 'activity_pub_model'):
            return value.activity_pub_model.pub_url
        elif hasattr(value, 'origin'):
            return value.origin.pub_url

    def _resolve(self, data):
        if isinstance(data, str):
            data = {'id': data}

        activity_pub_model = ActivityPubModel.objects.from_iri(data['id'])
        if activity_pub_model.is_local:
            return activity_pub_model.origin
        return adapter.adopt(activity_pub_model)

    def to_internal_value(self, data):
        obj = self._resolve(data)
        if self.source != '*':
            return obj
        if obj._meta.model_name.endswith('slot'):
            return {'slot': obj, 'activity': obj.activity}
        return {'activity': obj}


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
        return {'answer': data, 'motivation': data}


class JoinTeamField(serializers.Field):
    """Nested Team on a team-schedule Join."""

    def get_attribute(self, instance):
        teams = getattr(instance, 'teams', None)
        if teams is None:
            raise SkipField()
        return teams.first()

    def get_origin_value(self, instance):
        teams = getattr(instance, 'teams', None)
        if teams is None:
            return None
        return teams.first()

    def to_representation(self, team):
        if team is None:
            return None
        return FederatedTeamSerializer(instance=team).data

    def to_internal_value(self, data):
        if not data:
            return {}
        if isinstance(data, str):
            return {'id': data}
        return {
            'id': data.get('id') or data.get('iri'),
            'name': data.get('name'),
            'description': data.get('description') or data.get('summary'),
        }


class ContributorSerializer(FederatedObjectBaseSerializer):
    type = TypeField('Join')
    actor = FederatedMemberSerializer(source='*')
    object = RelatedActivityField(source='*')
    motivation = MotivationField(required=False, allow_null=True, source='*')
    team = JoinTeamField(required=False, allow_null=True)

    class Meta:
        model = Contributor
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'actor', 'object', 'motivation', 'team',
        )

    def get_polymorphic_serializer(self, validated_data):
        target = validated_data.get('slot') or validated_data['activity']
        model_name = target._meta.model_name

        if (
            model_name == 'scheduleactivity'
            and getattr(target, 'team_activity', None) == 'teams'
        ):
            serializer_class = TeamScheduleRegistrationSerializer
        else:
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
            serializer_class = serializer_mapping[model_name]

        serializer = serializer_class()
        serializer.parent = self
        return serializer

    def create(self, validated_data):
        validated_data.pop('id', None)
        validated_data.pop('type', None)
        return self.get_polymorphic_serializer(validated_data).create(validated_data)


class BaseContributorSerializer(FederatedObjectBaseSerializer):
    def get_queryset(self):
        return self.model.objects.all()

    def get_contributor(self, validated_data):
        filters = {'activity': validated_data['activity']}
        if validated_data.get('remote_user'):
            filters['remote_user'] = validated_data['remote_user']
        elif validated_data.get('user'):
            filters['user'] = validated_data['user']
        else:
            return None
        return self.get_queryset().filter(**filters).first()

    def update(self, contributor, validated_data):
        if contributor.status == 'withdrawn':
            try:
                contributor.states.reapply(save=True)
            except TransitionNotPossible:
                pass
        return contributor

    def create(self, validated_data):
        contributor = self.get_contributor(validated_data)
        if contributor:
            self.update(contributor, validated_data)
            return contributor

        create_kwargs = {
            key: value for key, value in validated_data.items()
            if key in {field.name for field in self.model._meta.fields}
        }
        return self.model.objects.create(**create_kwargs)


class DeedParticipantSerializer(BaseContributorSerializer):
    model = DeedParticipant


class CollectParticipantSerializer(BaseContributorSerializer):
    model = CollectContributor


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
        validated_data['registration'] = ScheduleRegistration.objects.get(
            activity=validated_data['activity'],
            user=validated_data['user']
        )
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
        validated_data['registration'] = PeriodicRegistration.objects.get(
            activity=validated_data['activity'],
            user=validated_data['user']
        )
        return super().create(validated_data)


class PeriodicRegistrationSerializer(BaseContributorSerializer):
    model = PeriodicRegistration


class DateRegistrationSerializer(BaseContributorSerializer):
    model = DateRegistration


class DateParticipantSerializer(BaseContributorSerializer):
    model = DateParticipant

    def get_contributor(self, validated_data):
        filters = {
            'activity': validated_data['activity'],
            'slot': validated_data['slot'],
        }
        if validated_data.get('remote_user'):
            filters['remote_user'] = validated_data['remote_user']
        elif validated_data.get('user'):
            filters['user'] = validated_data['user']
        else:
            return None
        return self.model.objects.filter(**filters).first()


class FederatedTeamSerializer(FederatedObjectBaseSerializer):
    type = TypeField('Team')
    name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    summary = serializers.CharField(
        source='description', required=False, allow_null=True, allow_blank=True
    )
    attributed_to = RelatedActivityField(source='activity')
    captain = FederatedMemberSerializer(source='*', required=False, allow_null=True)

    class Meta:
        model = LocalTeam
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'name', 'summary', 'attributed_to', 'captain',
        )

    def create(self, validated_data):
        answer = validated_data.pop('answer', None)
        iri = validated_data.pop('id', None)
        validated_data.pop('type', None)

        create_kwargs = {
            key: value for key, value in validated_data.items()
            if key in {field.name for field in self.Meta.model._meta.fields}
        }
        team = self.Meta.model(**create_kwargs)
        trigger_options = {}
        if answer is not None:
            trigger_options['answer'] = answer
        team.execute_triggers(**trigger_options)
        team.save()

        origin = ActivityPubModel.objects.from_iri(iri) if iri else None
        if origin and hasattr(origin, 'adopted') and not origin.adopted:
            origin.adopted = team
            origin.save()
        return team


class TeamScheduleRegistrationSerializer(BaseContributorSerializer):
    model = TeamScheduleRegistration

    def update(self, contributor, validated_data):
        team = contributor.teams.first()
        try:
            if team and team.status == 'withdrawn':
                team.states.rejoin(save=True)
            elif contributor.status == 'withdrawn':
                contributor.states.restore(save=True)
        except TransitionNotPossible:
            pass
        return contributor

    def create(self, validated_data):
        contributor = self.get_contributor(validated_data)
        if contributor:
            return self.update(contributor, validated_data)

        team_data = JoinTeamField().to_internal_value(
            validated_data.pop('team', None)
        )
        team = FederatedTeamSerializer().create({
            'id': team_data.get('id'),
            'activity': validated_data['activity'],
            'user': validated_data.get('user'),
            'remote_user': validated_data.get('remote_user'),
            'name': team_data.get('name'),
            'description': team_data.get('description'),
            'answer': validated_data.get('answer'),
        })
        return team.registration


class TeamScheduleRegistrationJoinSerializer(FederatedObjectBaseSerializer):
    """Outbound Join representation for a team schedule registration."""
    type = TypeField('Join')
    actor = MemberSerializer(source='user')
    object = RelatedActivityField(source='activity')
    motivation = serializers.CharField(
        source='answer', required=False, allow_null=True, allow_blank=True
    )
    team = JoinTeamField(required=False, allow_null=True)

    class Meta:
        model = TeamScheduleRegistration
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'actor', 'object', 'motivation', 'team',
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
        filters = {'activity': validated_data['activity']}
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

        slot = validated_data['slot']
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


class RelatedTeamField(RelatedField):
    required_message = 'Team is required'
    unknown_message = 'Unknown team'
    unresolved_message = 'Team could not be resolved'

    def get_queryset(self):
        return ActivityPubModel.objects.all()

    def get_origin_value(self, instance):
        return getattr(instance, 'team', None)

    def to_representation(self, value):
        if value is None:
            return None
        try:
            if value.origin:
                return value.origin.pub_url
        except (AttributeError, ObjectDoesNotExist):
            pass
        if hasattr(value, 'activity_pub_model'):
            return value.activity_pub_model.pub_url

    def to_internal_value(self, data):
        if data is None:
            raise serializers.ValidationError(self.required_message)
        if isinstance(data, str):
            data = {'id': data}
        elif isinstance(data, dict) and 'id' not in data and 'iri' in data:
            data = {'id': data['iri']}
        team_iri = data.get('id') or data.get('iri')
        if not team_iri:
            raise serializers.ValidationError(self.required_message)

        ap_team = ActivityPubModel.objects.from_iri(team_iri)
        if not isinstance(ap_team, ActivityPubTeam):
            raise serializers.ValidationError(self.unknown_message)
        if ap_team.is_local:
            team = ap_team.origin
        elif ap_team.adopted:
            team = ap_team.adopted
        else:
            team = adapter.adopt(ap_team)

        if team is None:
            raise serializers.ValidationError(self.unresolved_message)
        return team


class TeamMemberJoinSerializer(FederatedObjectBaseSerializer):
    type = TypeField('Join')
    actor = FederatedMemberSerializer(source='*')
    object = RelatedTeamField(source='team')

    class Meta:
        model = TeamMember
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'actor', 'object',
        )

    def to_internal_value(self, data):
        actor_iri = resource_iri(data.get('actor'))
        if actor_iri and is_local(actor_iri):
            raise serializers.ValidationError({
                'actor': 'Cannot join a team as a local person via remote Join',
            })
        return super().to_internal_value(data)

    def validate(self, attrs):
        team = attrs.get('team')
        if team is None:
            raise serializers.ValidationError({
                'object': 'Join object team is required',
            })

        event = event_for_team(team)
        if event is None:
            raise serializers.ValidationError({
                'object': 'Join object team is not attributed to an activity',
            })

        event_activity = event.origin if event.is_local else event.adopted
        if event_activity is None or event_activity.pk != team.activity_id:
            raise serializers.ValidationError({
                'object': 'Join object team does not belong to the attributed activity',
            })

        request = self.context.get('request') if self.context else None
        platform = sending_platform(
            request=request,
            activity_iri=resource_iri(self.initial_data.get('id')),
        )
        if platform is None:
            raise serializers.ValidationError(
                'Join platform could not be determined'
            )

        if not platform_may_modify_event(platform, event):
            raise serializers.ValidationError({
                'object': 'Platform is not authorized to add members to this team',
            })

        remote_user = attrs.get('remote_user')
        if remote_user is None:
            raise serializers.ValidationError({
                'actor': 'Join actor is required',
            })

        person = getattr(remote_user, 'origin', None)
        if (
            person is not None and
            person.source_id and
            person.source_id != platform.id
        ):
            raise serializers.ValidationError({
                'actor': 'Person does not belong to the sending platform',
            })

        return attrs

    def update(self, instance, validated_data):
        if instance.status != 'active':
            try:
                instance.states.resume(save=True)
            except TransitionNotPossible:
                pass
        return instance

    def create(self, validated_data):
        validated_data.pop('id', None)
        validated_data.pop('type', None)
        team = validated_data['team']
        remote_user = validated_data['remote_user']

        existing = TeamMember.objects.filter(
            team=team, remote_user=remote_user
        ).first()
        if existing:
            return self.update(existing, validated_data)

        member = TeamMember(team=team, user=None, remote_user=remote_user)
        member.execute_triggers()
        member.save()
        return member


class RelatedTeamSlotField(RelatedTeamField):
    required_message = 'Team is required for team schedule slots'


class TeamScheduleSlotsSerializer(ScheduleSlotsSerializer):
    type = TypeField('subEvent')
    team = RelatedTeamSlotField()
    status = serializers.CharField(read_only=True)

    class Meta(ScheduleSlotsSerializer.Meta):
        model = TeamScheduleSlot
        fields = ScheduleSlotsSerializer.Meta.fields + ('team',)

    def _team_slot_to_reuse(self, validated_data, instance=None):
        team = validated_data.get('team') or getattr(instance, 'team', None)
        if not team:
            raise serializers.ValidationError({
                'team': 'Team is required to adopt a team schedule slot',
            })
        validated_data['team'] = team
        return team.slots.order_by('pk').first() or instance

    def create(self, validated_data):
        existing = self._team_slot_to_reuse(validated_data)
        if existing:
            return self.update(existing, validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        iri = validated_data.get('id')
        instance = self._team_slot_to_reuse(validated_data, instance)
        result = super().update(instance, validated_data)
        origin = ActivityPubModel.objects.from_iri(iri) if iri else None
        if origin and hasattr(origin, 'adopted'):
            origin.adopted = result
            origin.save()
        return result
