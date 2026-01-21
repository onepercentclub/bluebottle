from io import BytesIO

import requests
from django.contrib.gis.geos import Point
from django.core.files import File
from django.db import models
from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer

from bluebottle.activity_links.models import LinkedActivity, LinkedDeed, LinkedDateActivity, LinkedDeadlineActivity, \
    LinkedFunding, LinkedDateSlot, LinkedCollectCampaign, LinkedPeriodicActivity
from bluebottle.geo.models import Geolocation, Country
from bluebottle.geo.serializers import GeolocationSerializer, PointSerializer, CountrySerializer
from bluebottle.utils.fields import RichTextField


class LinkedActivityImageField(serializers.Field):
    """Custom field to handle image conversion from JSON-LD format to File object"""

    def to_internal_value(self, data):
        if not data:
            return None

        if isinstance(data, dict):
            image_url = data.get('url') or data.get('id')
            image_name = data.get('name', 'image')
        else:
            image_url = data
            image_name = 'image'

        if not image_url:
            return None

        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            return File(BytesIO(response.content), name=image_name)
        except requests.exceptions.RequestException as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not fetch image from {image_url}: {e}")
            return None

    def to_representation(self, value):
        if not value:
            return None
        return value


class AddressSerializer(serializers.Serializer):
    street_address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    address_locality = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    address_region = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    address_country = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        fields = (
            'street_address', 'postal_code', 'address_locality', 'address_region', 'address_country',
        )


class LinkedLocationSerializer(GeolocationSerializer):
    address = AddressSerializer(write_only=True, required=False)
    name = serializers.CharField(source='formatted_address', write_only=True, required=False)
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)
    position = PointSerializer(read_only=True)
    country = CountrySerializer(read_only=True)

    def to_internal_value(self, data):
        if not data or not data['id']:
            return {}

        lat = data.pop('latitude', None)
        long = data.pop('longitude', None)
        if lat is not None and long is not None:
            data['position'] = Point(float(lat), float(long))
        else:
            data['position'] = None

        address = data.pop('address', {})
        if address and isinstance(address, dict):
            if address.get('address_country', None):
                country = Country.objects.filter(alpha2_code=address['address_country'].upper()).first()
                if country:
                    data['country'] = country
            data['province'] = address.get('address_region', None)
            data['locality'] = address.get('address_locality', None)
            data['postal_code'] = address.get('postal_code', None)
            data['street'] = address.get('street_address', None)

        if 'name' in data:
            data['formatted_address'] = data.pop('name', None)

        location = None
        if data.get('position'):
            location = Geolocation.objects.filter(position=data['position']).first()

        if location:
            data['id'] = location.id
        else:
            data['id'] = None
        return data

    class Meta:
        model = Geolocation
        fields = GeolocationSerializer.Meta.fields + ('address', 'name', 'longitude', 'latitude')


class LinkedLocationMixin(object):

    def _save_location(self, instance, location_data):
        location_obj = None
        if location_data is serializers.empty:
            return instance

        if location_data is None:
            instance.location = None
            instance.save(update_fields=['location'])
            return None

        loc_id = location_data.get('id', None)

        location_fields = dict(location_data)

        position = location_data.get('position', None)
        if position:
            location_fields['position'] = position

        if loc_id:
            location_obj = Geolocation.objects.select_for_update().get(id=loc_id)
            for attr, value in location_fields.items():
                if value is not None:
                    setattr(location_obj, attr, value)
            location_obj.save()
        else:
            if location_fields:
                location_obj = Geolocation.objects.create(**location_fields)
            else:
                location_obj = None
        return location_obj

    def create(self, validated_data):
        location_data = validated_data.pop('location', serializers.empty)
        instance = super().create(validated_data)
        instance.location = self._save_location(instance, location_data)
        instance.save(update_fields=['location'])
        return instance

    def update(self, instance, validated_data):
        location_data = validated_data.pop('location', serializers.empty)
        instance = super().update(instance, validated_data)
        instance.location = self._save_location(instance, location_data)
        instance.save(update_fields=['location'])
        return instance


class BaseLinkedActivitySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='title')
    summary = RichTextField(source='description')
    url = serializers.URLField(source='link')
    image = LinkedActivityImageField(required=False, allow_null=True)

    class Meta:
        model = LinkedActivity
        fields = ('name', 'summary', 'url', 'image')


class LinkedDeedSerializer(BaseLinkedActivitySerializer):
    end_time = serializers.DateTimeField(source='end', allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True)

    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedDeed
        fields = BaseLinkedActivitySerializer.Meta.fields + (
            'start_time', 'end_time'
        )


class LinkedCollectCampaignSerializer(LinkedLocationMixin, BaseLinkedActivitySerializer):
    end_time = serializers.DateTimeField(source='end', allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True)
    location = LinkedLocationSerializer(required=False, allow_null=True)

    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedCollectCampaign
        fields = BaseLinkedActivitySerializer.Meta.fields + (
            'start_time', 'end_time', 'location', 'location_hint', 'collect_type'
        )


class LinkedSlotSerializer(LinkedLocationMixin, BaseLinkedActivitySerializer):
    end_time = serializers.DateTimeField(source='end', allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True)
    location = LinkedLocationSerializer(required=False, allow_null=True)

    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedDateSlot
        fields = (
            'start_time', 'end_time',
            'location'
        )


class LinkedDateActivitySerializer(BaseLinkedActivitySerializer):
    sub_event = LinkedSlotSerializer(source='slots', many=True)

    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedDateActivity
        fields = BaseLinkedActivitySerializer.Meta.fields + ('sub_event',)

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


class LinkedDeadlineActivitySerializer(LinkedLocationMixin, BaseLinkedActivitySerializer):
    end_time = serializers.DateTimeField(source='end', allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True)
    location = LinkedLocationSerializer(required=False, allow_null=True)

    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedDeadlineActivity
        fields = BaseLinkedActivitySerializer.Meta.fields + ('start_time', 'end_time', 'location')


class LinkedPeriodicActivitySerializer(LinkedLocationMixin, BaseLinkedActivitySerializer):
    end_time = serializers.DateTimeField(source='end', allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True)
    location = LinkedLocationSerializer(required=False, allow_null=True)

    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedPeriodicActivity
        fields = BaseLinkedActivitySerializer.Meta.fields + (
            'start_time', 'end_time', 'location',
            'duration', 'repetition'
        )


class LinkedRegisteredDateActivitySerializer(LinkedLocationMixin, BaseLinkedActivitySerializer):
    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedDeadlineActivity


class LinkedFundingSerializer(LinkedLocationMixin, BaseLinkedActivitySerializer):
    end_time = serializers.DateTimeField(source='end', allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True)
    location = LinkedLocationSerializer(required=False, allow_null=True)

    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedFunding
        fields = BaseLinkedActivitySerializer.Meta.fields + (
            'target', 'donated',
            'start_time', 'end_time', 'location'
        )


class LinkedActivitySerializer(PolymorphicSerializer):
    resource_type_field_name = 'type'

    polymorphic_serializers = [
        LinkedDeedSerializer,
        LinkedDateActivitySerializer,
        LinkedDeadlineActivitySerializer,
        LinkedPeriodicActivitySerializer,
        LinkedRegisteredDateActivitySerializer,
        LinkedFundingSerializer,
        LinkedCollectCampaignSerializer,
    ]

    model_type_mapping = {
        LinkedDeed: 'GoodDeed',
        LinkedDateActivity: 'DoGoodEvent',
        LinkedPeriodicActivity: 'DoGoodEvent',
        LinkedDeadlineActivity: 'DoGoodEvent',
        LinkedFunding: 'Funding',
        LinkedCollectCampaign: 'CollectCampaign'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource_type_model_mapping['DateActivity'] = LinkedDateActivity
        self.resource_type_model_mapping['DeadlineActivity'] = LinkedDeadlineActivity
        self.resource_type_model_mapping['PeriodicActivity'] = LinkedPeriodicActivity
        self.resource_type_model_mapping['RegisteredDateActivity'] = LinkedDeadlineActivity
        self.resource_type_model_mapping['Funding'] = LinkedFunding
        self.resource_type_model_mapping['GoodDeed'] = LinkedDeed
        self.resource_type_model_mapping['CollectCampaign'] = LinkedCollectCampaign

    def _get_resource_type_from_mapping(self, data):
        event_type = data.get('type')

        # Map CrowdFunding to Funding for LinkedFunding
        if event_type == 'CrowdFunding':
            return 'Funding'

        # Handle DoGoodEvent - check sub_event to distinguish DateActivity from DeadlineActivity
        if event_type == 'DoGoodEvent':
            if data.get('repetition', 'once') not in ['once', None]:
                return 'PeriodicActivity'
            if data.get('join_mode', None) == 'selected':
                return 'RegisteredDateActivity'
            if len(data.get('sub_event', [])) > 0:
                return 'DateActivity'
            else:
                return 'DeadlineActivity'

        # For GoodDeed, return as-is
        if event_type == 'GoodDeed':
            return 'GoodDeed'

        return super()._get_resource_type_from_mapping(data)

    def to_resource_type(self, model_or_instance):
        if isinstance(model_or_instance, models.Model):
            model = type(model_or_instance)
        else:
            model = model_or_instance
        return self.model_type_mapping[model]

    model_serializer_mapping = {
        LinkedDeed: LinkedDeedSerializer,
        LinkedDateActivity: LinkedDateActivitySerializer,
        LinkedDeadlineActivity: LinkedDeadlineActivitySerializer,
        LinkedFunding: LinkedFundingSerializer,
        LinkedCollectCampaign: LinkedCollectCampaignSerializer,
        LinkedPeriodicActivity: LinkedPeriodicActivitySerializer
    }

    class Meta:
        model = LinkedActivity
