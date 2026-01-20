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
from rest_polymorphic.serializers import PolymorphicSerializer

from bluebottle.collect.models import CollectActivity, CollectType
from bluebottle.utils.models import get_default_language

logger = logging.getLogger(__name__)

from bluebottle.activity_pub.serializers.base import FederatedObjectSerializer
from bluebottle.activity_pub.serializers.fields import FederatedIdField

from bluebottle.activity_pub.models import EventAttendanceModeChoices, Image as ActivityPubImage, JoinModeChoices, \
    SubEvent
from bluebottle.deeds.models import Deed
from bluebottle.files.models import Image
from bluebottle.files.serializers import ORIGINAL_SIZE
from bluebottle.funding.models import Funding
from bluebottle.geo.models import Country, Geolocation
from bluebottle.organizations.models import Organization
from bluebottle.time_based.models import DateActivitySlot, DeadlineActivity, DateActivity
from bluebottle.utils.fields import RichTextField

from rest_framework import serializers


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

    address_locality = serializers.CharField(source='locality', required=False, allow_null=True)
    address_region = serializers.CharField(source='province', required=False, allow_null=True)
    address_country = CountryField(source='country.code', required=False, allow_null=True)

    class Meta:
        model = Geolocation
        fields = (
            'id', 'street_address', 'postal_code', 'address_locality',
            'address_region', 'address_country'
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
    logo = ImageField(required=False, allow_null=True)

    class Meta:
        model = Organization
        fields = ('id', 'name', 'summary', 'logo')


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
    summary = RichTextField(source='description')
    image = ImageSerializer(required=False, allow_null=True)
    organization = OrganizationSerializer(required=False, allow_null=True)
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return connection.tenant.build_absolute_url(
            obj.get_absolute_url()
        )

    class Meta:
        fields = FederatedObjectSerializer.Meta.fields + (
            'name', 'summary', 'image', 'organization', 'url'
        )

    def save(self, *args, **kwargs):
        if not kwargs.get('owner'):
            kwargs['owner'] = self.context['request'].user

        return super().save(**kwargs)


class FederatedDeedSerializer(BaseFederatedActivitySerializer):
    id = FederatedIdField('json-ld:good-deed')
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
        print('translated', translated)
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
    amount = serializers.FloatField(source='realized', allow_null=True, required=False)
    location = LocationSerializer(allow_null=True, required=False)
    location_hint = serializers.CharField(allow_null=True, allow_blank=True, required=False, max_length=500)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = CollectActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'start_time', 'end_time',
            'collect_type', 'target', 'amount', 'realized',
            'location', 'location_hint'
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
        kwargs['source'] = 'review'
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


class FederatedDeadlineActivitySerializer(BaseFederatedActivitySerializer):
    id = FederatedIdField('json-ld:crowd-funding')

    location = LocationSerializer(allow_null=True, required=False)

    start_time = DateField(source='start', allow_null=True)
    end_time = DateField(source='deadline', allow_null=True)
    registration_deadline = DateField(allow_null=True)

    event_attendance_mode = EventAttendanceModeField()
    join_mode = JoinModeField()
    duration = serializers.DurationField(allow_null=True)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = DeadlineActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'location', 'start_time', 'end_time', 'registration_deadline',
            'event_attendance_mode', 'duration', 'join_mode',
        )


class SlotsSerializer(FederatedObjectSerializer):
    id = FederatedIdField('json-ld:sub-event')

    name = serializers.CharField(source='title', required=False, allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True, required=False)
    end_time = serializers.DateTimeField(source='end', read_only=True)
    location = LocationSerializer(allow_null=True, required=False)

    event_attendance_mode = EventAttendanceModeField()

    duration = serializers.DurationField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        kwargs['source'] = 'slots'

        super().__init__(*args, **kwargs)

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
        fields = FederatedObjectSerializer.Meta.fields + (
            'name', 'location', 'start_time', 'end_time',
            'event_attendance_mode', 'duration',
        )


class FederatedDateActivitySerializer(BaseFederatedActivitySerializer):
    id = FederatedIdField('json-ld:do-good-event')

    sub_event = SlotsSerializer(many=True, source='slots')
    join_mode = JoinModeField()
    registration_deadline = DateField(allow_null=True)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = DateActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'sub_event', 'review', 'join_mode', 'registration_deadline',
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


class FederatedActivitySerializer(PolymorphicSerializer):
    resource_type_field_name = 'type'

    polymorphic_serializers = [
        FederatedDeadlineActivitySerializer,
        FederatedDeedSerializer,
        FederatedDateActivitySerializer,
        FederatedFundingSerializer,
        FederatedCollectSerializer
    ]

    model_type_mapping = {
        Deed: 'GoodDeed',
        Funding: 'CrowdFunding',
        DateActivity: 'DoGoodEvent',
        DeadlineActivity: 'DoGoodEvent',
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

    def to_resource_type(self, model_or_instance):
        if isinstance(model_or_instance, models.Model):
            model = type(model_or_instance)
        else:
            model = model_or_instance

        return self.model_type_mapping[model]

    def _get_resource_type_from_mapping(self, data):
        if data.get('type') == 'DoGoodEvent':
            if len(data.get('sub_event', [])) > 0:
                return 'DateActivity'
            else:
                return 'DeadlineActivity'

        return super()._get_resource_type_from_mapping(data)

    def save(self, *args, **kwargs):
        if not kwargs.get('owner'):
            kwargs['owner'] = self.context['request'].user

        return super().save(**kwargs)
