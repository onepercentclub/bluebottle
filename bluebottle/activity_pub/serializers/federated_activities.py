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
from rest_framework.relations import RelatedField

from bluebottle.activity_pub.models import (
    EventAttendanceModeChoices, Image as ActivityPubImage, JoinModeChoices,
    RepetitionModeChoices, SlotModeChoices, Create, ActivityPubModel
)
from bluebottle.activity_pub.serializers.base import FederatedObjectBaseSerializer
from bluebottle.activity_pub.serializers.fields import FederatedIdField, TypeField
from bluebottle.activities.models import Contributor, RemoteMember
from bluebottle.collect.models import CollectActivity, CollectType, CollectContributor
from bluebottle.members.models import Member
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.files.models import Image
from bluebottle.files.serializers import ORIGINAL_SIZE
from bluebottle.funding.models import Funding
from bluebottle.geo.models import Country, Geolocation
from bluebottle.grant_management.models import GrantApplication
from bluebottle.organizations.models import Organization
from bluebottle.time_based.models import (
    DateActivitySlot, DateParticipant, DateRegistration, DeadlineActivity, DateActivity,
    DeadlineRegistration, PeriodicRegistration, RegisteredDateActivity,
    PeriodicActivity, Registration, ScheduleActivity, ScheduleRegistration, ScheduleSlot
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
        if len(instance.activity_set.all()) > 0:
            return connection.tenant.build_absolute_url(
                reverse('activity-image', args=(instance.activity_set.first().pk, ORIGINAL_SIZE))
            )
        else:
            __import__('ipdb').set_trace()

    def create(self, validated_data):
        if not validated_data:
            return None

        image = ActivityPubImage.objects.from_iri(validated_data['id'])

        response = requests.get(image.url, timeout=30)
        response.raise_for_status()

        validated_data['file'] = File(BytesIO(response.content), name=validated_data['name'] or '')

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

    def create(self, validated_data):
        source = Create.objects.get(object__iri=validated_data['id']).actor
        follow = source.follow_set.get()
        if follow.default_owner:
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
    donated = serializers.DecimalField(source='amount_donated.amount', decimal_places=2, max_digits=10)
    donated_currency = serializers.CharField(source='amount_donated.currency')

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = Funding
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'location', 'end_time',
            'target', 'target_currency',
            'donated', 'donated_currency'
        )

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)
        if internal_value.get('target'):
            internal_value['target'] = Money(
                **internal_value['target']
            )
        if internal_value.get('amount_donated'):
            internal_value['amount_donated'] = Money(
                **internal_value['amount_donated']
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

        return ActivityPubModel.objects.from_iri(data['id'])


class DateSlotsSerializer(FederatedObjectBaseSerializer):
    type = TypeField('subEvent')

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

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = ScheduleSlot
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'name', 'location', 'start_time', 'end_time',
            'event_attendance_mode', 'duration', 'capacity',
            'status', 'location_hint', 'online_meeting_url',
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
                    instance.slots.get(origin__iri=slot.pop('id')),
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
    slot_mode = serializers.SerializerMethodField()

    def get_slot_mode(self, obj):
        return SlotModeChoices.scheduled

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = ScheduleActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'location', 'start_time', 'end_time', 'application_deadline',
            'event_attendance_mode', 'duration', 'join_mode', 'slot_mode'
        )


class RelatedActivityField(RelatedField):
    def get_queryset(self):
        # TODO: filter queryset on correct types
        return ActivityPubModel.objects.all()

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

        return ActivityPubModel.objects.from_iri(data['id']).origin


class RegistrationSerializer(FederatedObjectBaseSerializer):
    type = TypeField('Join')
    actor = MemberSerializer(source='user')
    object = RelatedActivityField(source='activity')

    class Meta:
        model = Registration
        fields = FederatedObjectBaseSerializer.Meta.fields + (
            'actor', 'object',
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
        serializer_mapping = {
            'deed': DeedParticipantSerializer,
            'collectactivity': CollectParticipantSerializer,
            'deadlineactivity': DeadlineParticipantSerializer,
            'scheduleactivity': ScheduleParticipantSerializer,
            'periodicactivity': PeriodicParticipantSerializer,
            'dateactivityslot': DateParticipantSerializer,
        }

        return serializer_mapping[validated_data['activity']._meta.model_name]()

    def create(self, validated_data):
        validated_data.pop('id')
        validated_data.pop('user')

        field = self.fields['actor']
        field.initial_data = self.initial_data['actor']
        field.is_valid(raise_exception=True)
        validated_data['remote_user'] = field.save()

        polymorphic_serializer = self.get_polymorphic_serializer(validated_data)
        return polymorphic_serializer.create(validated_data)


class BaseContributorSerializer(FederatedObjectBaseSerializer):
    def get_contributor(self, validated_data):
        return self.model.objects.filter(
            activity=validated_data['activity'],
            remote_user=validated_data['remote_user'],
        ).first()

    def create(self, validated_data):
        contributor = self.get_contributor(validated_data)
        if contributor:
            contributor.states.reapply(save=True)
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


class ScheduleParticipantSerializer(BaseContributorSerializer):
    model = ScheduleRegistration

    def get_contributor(self, validated_data):
        contributor = super().get_contributor(validated_data)
        if contributor:
            return contributor.participants.first()


class PeriodicParticipantSerializer(BaseContributorSerializer):
    model = PeriodicRegistration


class DateParticipantSerializer(BaseContributorSerializer):
    model = DateParticipant

    def create(self, validated_data):
        slot = validated_data.pop('activity')

        validated_data['registration'] = DateRegistration.objects.create(
            activity=slot.activity,
            **validated_data
        )

        validated_data['slot'] = slot
        validated_data['activity'] = slot.activity

        validated_data.pop('answer')

        return super().create(validated_data)
