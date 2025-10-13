import datetime
from io import BytesIO

import pytz
import requests
from django.contrib.gis.geos import Point
from django.core.files import File
from django.db import connection, models
from django.urls import reverse
from rest_framework import serializers, exceptions
from rest_polymorphic.serializers import PolymorphicSerializer

from bluebottle.activity_pub.models import EventAttendanceModeChoices, Image as ActivityPubImage
from bluebottle.activity_pub.serializers.base import (
    FederatedObjectSerializer
)
from bluebottle.deeds.models import Deed
from bluebottle.files.models import Image
from bluebottle.files.serializers import ORIGINAL_SIZE
from bluebottle.funding.models import Funding
from bluebottle.geo.models import Country, Geolocation
from bluebottle.organizations.models import Organization
from bluebottle.time_based.models import DateActivitySlot, DeadlineActivity, DateActivity
from bluebottle.utils.fields import RichTextField
from bluebottle.utils.serializers import Money


class IdField(serializers.CharField):
    def __init__(self, url_name):
        self.url_name = url_name
        super().__init__(source='*')

    def to_representation(self, value):
        return value.activity_pub_url

    def to_internal_value(self, value):
        return {'id': value}


class ImageSerializer(FederatedObjectSerializer):
    id = IdField('json-ld:image')
    url = serializers.SerializerMethodField()
    name = serializers.CharField()

    def get_url(self, instance):
        return connection.tenant.build_absolute_url(
            reverse('activity-image', args=(instance.activity_set.first().pk, ORIGINAL_SIZE))
        )

    def create(self, validated_data):
        if not validated_data:
            return None
        validated_data['owner'] = self.context['request'].user
        image = ActivityPubImage.objects.get(iri=validated_data['id'])
        response = requests.get(image.url, timeout=30)
        response.raise_for_status()

        validated_data['file'] = File(BytesIO(response.content), name=validated_data['name'])

        return super().create(validated_data)

    class Meta:
        model = Image
        fields = FederatedObjectSerializer.Meta.fields + (
            'url', 'name'
        )


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
    id = IdField('json-ld:address')

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


class OrganizationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(allow_null=True)
    summary = serializers.CharField(
        source='description',
        allow_blank=True,
        allow_null=True,
        required=False
    )

    class Meta:
        model = Organization
        fields = ('name', 'summary')


class LocationSerializer(FederatedObjectSerializer):
    id = IdField('json-ld:place')
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

    class Meta:
        fields = FederatedObjectSerializer.Meta.fields + ('name', 'summary', 'image', 'organization')

    def create(self, validated_data):
        organization_data = validated_data.pop('organization', None)
        if organization_data:
            organization_serializer = OrganizationSerializer(data=organization_data)
            organization_serializer.is_valid(raise_exception=True)
            validated_data['organization'] = organization_serializer.save()

        return super().create(validated_data)


class FederatedDeedSerializer(BaseFederatedActivitySerializer):
    id = IdField('json-ld:good-deed')
    start_time = DateField(source='start', allow_null=True)
    end_time = DateField(source='end', allow_null=True)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = Deed
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'start_time', 'end_time'
        )


class FederatedFundingSerializer(BaseFederatedActivitySerializer):
    id = IdField('json-ld:crowd-funding')

    location = LocationSerializer(source='impact_location', allow_null=True, required=False)

    end_time = serializers.DateTimeField(source='deadline')
    target = serializers.DecimalField(source='target.amount', decimal_places=2, max_digits=10)
    target_currency = serializers.CharField(source='target.currency')

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = Funding
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'location', 'end_time', 'target', 'target_currency'
        )

    def create(self, validated_data):
        if validated_data.get('target'):
            validated_data['target'] = Money(**validated_data['target'])

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


class FederatedDeadlineActivitySerializer(BaseFederatedActivitySerializer):
    id = IdField('json-ld:crowd-funding')

    location = LocationSerializer(allow_null=True, required=False)

    start_time = DateField(source='start', allow_null=True)
    end_time = DateField(source='deadline', allow_null=True)

    event_attendance_mode = EventAttendanceModeField()
    duration = serializers.DurationField(allow_null=True)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = DeadlineActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + (
            'location', 'start_time', 'end_time', 'event_attendance_mode', 'duration',
        )


class SlotsSerializer(FederatedObjectSerializer):
    id = IdField('json-ld:sub-event')

    name = serializers.CharField(source='title', required=False, allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True, required=False)
    end_time = serializers.DateTimeField(source='end', read_only=True)
    location = LocationSerializer(allow_null=True, required=False)

    event_attendance_mode = EventAttendanceModeField()

    duration = serializers.DurationField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        kwargs['source'] = 'slots'

        super().__init__(*args, **kwargs)

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = DateActivitySlot

        fields = FederatedObjectSerializer.Meta.fields + (
            'name', 'location', 'start_time', 'end_time', 'event_attendance_mode', 'duration',
        )


class FederatedDateActivitySerializer(BaseFederatedActivitySerializer):
    id = IdField('json-ld:do-good-event')

    sub_event = SlotsSerializer(many=True, source='slots')

    class Meta(BaseFederatedActivitySerializer.Meta):
        model = DateActivity
        fields = BaseFederatedActivitySerializer.Meta.fields + ('sub_event', )

    def create(self, validated_data):
        slots = validated_data.pop('slots', [])
        result = super().create(validated_data)

        field = self.fields['sub_event']
        for slot in slots:
            slot['activity'] = result

        validated_data[field.source] = field.create(slots)

        return result


class FederatedActivitySerializer(PolymorphicSerializer):
    resource_type_field_name = 'type'

    polymorphic_serializers = [
        FederatedDeadlineActivitySerializer,
        FederatedDeedSerializer,
        FederatedDateActivitySerializer,
        FederatedFundingSerializer
    ]

    model_type_mapping = {
        Deed: 'GoodDeed',
        Funding: 'CrowdFunding',
        DateActivity: 'DoGoodEvent',
        DeadlineActivity: 'DoGoodEvent',
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
