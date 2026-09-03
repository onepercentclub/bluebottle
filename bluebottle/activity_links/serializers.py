from io import BytesIO

import requests
from django.contrib.gis.geos import Point
from django.core.files import File
from django.db import models
from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer

from bluebottle.activity_links.models import (
    LinkedActivity, LinkedDeed, LinkedDateActivity, LinkedDeadlineActivity,
    LinkedFunding, LinkedDateSlot, LinkedCollectCampaign, LinkedPeriodicActivity,
    LinkedScheduleActivity, LinkedGrantApplication
)
from bluebottle.activity_pub.models import Image as ActivityPubImage
from bluebottle.files.models import Image
from bluebottle.geo.models import Geolocation, Country
from bluebottle.geo.serializers import GeolocationSerializer
from bluebottle.utils.fields import RichTextField


class LinkedActivityImageSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    url = serializers.CharField()
    name = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    def create(self, validated_data):
        image = ActivityPubImage.objects.from_iri(validated_data['id'])

        response = requests.get(image.url, timeout=30)
        response.raise_for_status()

        file = File(BytesIO(response.content), name=validated_data['name'])

        return super().create({
            'file': file,
            'name': validated_data['name']
        })

    def update(self, instance, validated_data):
        image = ActivityPubImage.objects.from_iri(validated_data['id'])

        response = requests.get(image.url, timeout=30)
        response.raise_for_status()

        file = File(BytesIO(response.content), name=validated_data['name'])

        return super().update(instance, {
            'file': file,
            'name': validated_data['name']
        })

    class Meta:
        model = Image
        fields = ('id', 'url', 'name')


class AddressSerializer(serializers.Serializer):
    street_address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    locality = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    region = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    country = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        fields = (
            'street_address', 'postal_code', 'locality', 'region', 'country',
        )


class LinkedLocationSerializer(GeolocationSerializer):
    address = AddressSerializer(write_only=True, required=False)
    name = serializers.CharField(source='formatted_address', write_only=True, required=False)
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)

    def to_internal_value(self, data):
        result = dict(**super().to_internal_value(data))

        address = result['address']

        country = Country.objects.filter(alpha2_code=address['country']).first()

        return {
            'position': Point(
                result['longitude'], result['latitude']
            ),
            'formatted_address': result['formatted_address'],
            'locality': address['locality'],
            'street': address['street_address'],
            'postal_code': address['postal_code'],
            'country': country
        }

    class Meta:
        model = Geolocation
        fields = (
            'address', 'name', 'longitude', 'latitude'
        )


class BaseLinkedActivitySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='title')
    summary = RichTextField(source='description')
    url = serializers.URLField(source='link')
    image = LinkedActivityImageSerializer(required=False, allow_null=True)

    class Meta:
        model = LinkedActivity
        fields = ('name', 'summary', 'url', 'image')

    def create(self, validated_data):
        image_data = validated_data.pop('image', None)
        if image_data:
            # This one is also redundant, but not shape-breaking
            validated_data['image'] = LinkedActivityImageSerializer().create(image_data)

        location_data = validated_data.pop('location', None)
        if location_data:
            validated_data['location'] = Geolocation.objects.create(**location_data)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_data = validated_data.pop('image', None)
        if image_data:
            image_instance = getattr(instance, 'image', None)
            if image_instance:
                validated_data['image'] = LinkedActivityImageSerializer().update(image_instance, image_data)
            else:
                validated_data['image'] = LinkedActivityImageSerializer().create(image_data)

        location_data = validated_data.pop('location', None)
        if location_data:
            location_instance = getattr(instance, 'location', None)
            if location_instance:
                for k, v in location_data.items():
                    setattr(location_instance, k, v)
                location_instance.save()
                validated_data['location'] = location_instance
            else:
                validated_data['location'] = Geolocation.objects.create(**location_data)

        return super().update(instance, validated_data)


class LinkedDeedSerializer(BaseLinkedActivitySerializer):
    end_time = serializers.DateTimeField(source='end', allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True)

    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedDeed
        fields = BaseLinkedActivitySerializer.Meta.fields + (
            'start_time', 'end_time'
        )


class LinkedCollectCampaignSerializer(BaseLinkedActivitySerializer):
    end_time = serializers.DateTimeField(source='end', allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True)
    location = LinkedLocationSerializer(required=False, allow_null=True)

    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedCollectCampaign
        fields = BaseLinkedActivitySerializer.Meta.fields + (
            'start_time', 'end_time', 'location', 'location_hint', 'collect_type'
        )


class LinkedSlotSerializer(BaseLinkedActivitySerializer):
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


class LinkedDeadlineActivitySerializer(BaseLinkedActivitySerializer):
    end_time = serializers.DateTimeField(source='end', allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True)
    location = LinkedLocationSerializer(required=False, allow_null=True)

    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedDeadlineActivity
        fields = BaseLinkedActivitySerializer.Meta.fields + (
            'start_time', 'end_time', 'location', 'duration'
        )


class PeriodChoiceField(serializers.CharField):
    mapping = {
        "days": "DailyRepetitionMode",
        "weeks": "WeeklyRepetitionMode",
        "months": "MonthlyRepetitionMode",
    }

    def to_representation(self, value):
        return self.mapping[value]

    def to_internal_value(self, data):
        for k, v in self.mapping.items():
            if v in data:
                return k


class LinkedPeriodicActivitySerializer(BaseLinkedActivitySerializer):
    end_time = serializers.DateTimeField(source='end', allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True)
    location = LinkedLocationSerializer(required=False, allow_null=True)
    repetition_mode = PeriodChoiceField(source='period')

    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedPeriodicActivity
        fields = BaseLinkedActivitySerializer.Meta.fields + (
            'start_time', 'end_time', 'location',
            'duration', 'repetition_mode'
        )


class LinkedScheduleActivitySerializer(BaseLinkedActivitySerializer):
    end_time = serializers.DateTimeField(source='end', allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True)
    location = LinkedLocationSerializer(required=False, allow_null=True)

    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedScheduleActivity
        fields = BaseLinkedActivitySerializer.Meta.fields + (
            'start_time', 'end_time', 'location',
            'duration'
        )


class LinkedRegisteredDateActivitySerializer(BaseLinkedActivitySerializer):
    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedDeadlineActivity


class LinkedFundingSerializer(BaseLinkedActivitySerializer):
    end_time = serializers.DateTimeField(source='end', allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True)
    location = LinkedLocationSerializer(required=False, allow_null=True)

    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedFunding
        fields = BaseLinkedActivitySerializer.Meta.fields + (
            'target', 'donated',
            'start_time', 'end_time', 'location'
        )


class LinkedGrantApplicationSerializer(BaseLinkedActivitySerializer):
    end_time = serializers.DateTimeField(source='end', allow_null=True)
    start_time = serializers.DateTimeField(source='start', allow_null=True)
    location = LinkedLocationSerializer(required=False, allow_null=True)

    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedGrantApplication
        fields = BaseLinkedActivitySerializer.Meta.fields + (
            'target',
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
        LinkedScheduleActivitySerializer,
        LinkedFundingSerializer,
        LinkedGrantApplicationSerializer,
        LinkedCollectCampaignSerializer,
    ]

    model_type_mapping = {
        LinkedDeed: 'GoodDeed',
        LinkedDateActivity: 'DoGoodEvent',
        LinkedPeriodicActivity: 'DoGoodEvent',
        LinkedDeadlineActivity: 'DoGoodEvent',
        LinkedFunding: 'Funding',
        LinkedGrantApplication: 'GrantApplication',
        LinkedCollectCampaign: 'CollectCampaign',
        LinkedScheduleActivity: 'ScheduleActivity',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource_type_model_mapping['DateActivity'] = LinkedDateActivity
        self.resource_type_model_mapping['DeadlineActivity'] = LinkedDeadlineActivity
        self.resource_type_model_mapping['PeriodicActivity'] = LinkedPeriodicActivity
        self.resource_type_model_mapping['RegisteredDateActivity'] = LinkedDeadlineActivity
        self.resource_type_model_mapping['ScheduleActivity'] = LinkedScheduleActivity
        self.resource_type_model_mapping['Funding'] = LinkedFunding
        self.resource_type_model_mapping['GrantApplication'] = LinkedGrantApplication
        self.resource_type_model_mapping['GoodDeed'] = LinkedDeed
        self.resource_type_model_mapping['CollectCampaign'] = LinkedCollectCampaign

    def _get_resource_type_from_mapping(self, data):
        event_type = data.get('type')

        # Map CrowdFunding to Funding for LinkedFunding
        if event_type == 'CrowdFunding':
            return 'Funding'

        if event_type == 'GrantApplication':
            return 'GrantApplication'

        # Handle DoGoodEvent - check sub_event to distinguish DateActivity from DeadlineActivity
        if event_type == 'DoGoodEvent':
            if data.get('slot_mode', 'SetSlotMode') == 'ScheduledSlotMode':
                return 'ScheduleActivity'
            elif data.get('slot_mode', 'SetSlotMode') == 'PeriodicSlotMode':
                return 'PeriodicActivity'
            elif data.get('join_mode', None) == 'SelectedJoinMode':
                return 'RegisteredDateActivity'
            elif len(data.get('sub_event', [])) > 0:
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
        LinkedGrantApplication: LinkedGrantApplicationSerializer,
        LinkedCollectCampaign: LinkedCollectCampaignSerializer,
        LinkedPeriodicActivity: LinkedPeriodicActivitySerializer,
        LinkedScheduleActivity: LinkedScheduleActivitySerializer,
    }

    class Meta:
        model = LinkedActivity
