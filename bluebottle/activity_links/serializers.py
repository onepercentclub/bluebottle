from datetime import datetime
from io import BytesIO

import requests
from django.core.files import File
from django.db import models
from django.utils.timezone import localtime, now
from rest_framework import serializers
from rest_framework_json_api import serializers as json_api_serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_polymorphic.serializers import PolymorphicSerializer

from bluebottle.activity_links.models import (
    LinkedActivity, LinkedDeed, LinkedDateActivity, LinkedDeadlineActivity,
    LinkedFunding, LinkedDateSlot, LinkedCollectCampaign, LinkedPeriodicActivity,
    LinkedScheduleActivity, LinkedGrantApplication
)
from bluebottle.activity_pub.models import Image as ActivityPubImage
from bluebottle.activity_pub.serializers.fields import MapboxIdField
from bluebottle.files.models import Image
from bluebottle.files.serializers import IMAGE_SIZES, ImageField, ImageSerializer
from bluebottle.fsm.serializers import CurrentStatusField
from bluebottle.geo.models import Geolocation, Country
from bluebottle.geo.serializers import GeolocationSerializer, PointSerializer
from bluebottle.utils.fields import RichTextField
from bluebottle.utils.serializers import MoneySerializer


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


class LatLongPositionField(PointSerializer):
    def get_value(self, dictionary):
        if not isinstance(dictionary, dict):
            return serializers.empty
        if 'latitude' not in dictionary and 'longitude' not in dictionary:
            return serializers.empty
        return {
            'latitude': dictionary.get('latitude'),
            'longitude': dictionary.get('longitude'),
        }


class AddressSerializer(serializers.Serializer):
    street_address = serializers.CharField(
        source='street', required=False, allow_null=True, allow_blank=True
    )
    postal_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    locality = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    region = serializers.CharField(
        source='province', required=False, allow_null=True, allow_blank=True
    )
    country = serializers.SlugRelatedField(
        queryset=Country.objects.all(),
        slug_field='alpha2_code',
        required=False,
        allow_null=True,
    )


class LinkedLocationSerializer(GeolocationSerializer):
    address = AddressSerializer(source='*', write_only=True, required=False)
    name = serializers.CharField(
        source='formatted_address', write_only=True, required=False, allow_null=True
    )
    position = LatLongPositionField(write_only=True, required=False)
    identifier = MapboxIdField(source='mapbox_id', write_only=True, required=False)

    def validate(self, attrs):
        if not attrs.get('locality'):
            attrs['locality'] = attrs.get('formatted_address')
        return attrs

    class Meta:
        model = Geolocation
        fields = (
            'address', 'name', 'position', 'identifier',
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


class LocalDateField(serializers.DateField):
    def to_representation(self, value):
        if isinstance(value, datetime):
            value = localtime(value).date()
        return super().to_representation(value)


class LinkedActivityImageJSONAPISerializer(ImageSerializer):
    sizes = IMAGE_SIZES
    content_view_name = 'activity-links:image'
    relationship = 'linkedactivity_set'


class BaseLinkedActivityJSONAPISerializer(json_api_serializers.ModelSerializer):
    description = RichTextField()
    image = ImageField(required=False, allow_null=True)
    host_organization = ResourceRelatedField(read_only=True)
    current_status = CurrentStatusField(source='states.current_state')

    class Meta:
        model = LinkedActivity
        fields = (
            'id', 'title', 'description', 'link', 'current_status', 'archived',
            'image', 'host_organization',
        )
        meta_fields = ('current_status', )
        read_only_fields = fields

    class JSONAPIMeta:
        included_resources = ['image', 'host_organization']

    included_serializers = {
        'image': 'bluebottle.activity_links.serializers.LinkedActivityImageJSONAPISerializer',
        'host_organization': 'bluebottle.organizations.serializers.OrganizationSerializer',
    }


class LinkedActivityWithLocationJSONAPISerializer(BaseLinkedActivityJSONAPISerializer):
    location = ResourceRelatedField(read_only=True)

    class Meta(BaseLinkedActivityJSONAPISerializer.Meta):
        fields = BaseLinkedActivityJSONAPISerializer.Meta.fields + ('location', )
        read_only_fields = fields

    class JSONAPIMeta(BaseLinkedActivityJSONAPISerializer.JSONAPIMeta):
        included_resources = BaseLinkedActivityJSONAPISerializer.JSONAPIMeta.included_resources + [
            'location'
        ]

    included_serializers = dict(
        BaseLinkedActivityJSONAPISerializer.included_serializers,
        location='bluebottle.geo.serializers.GeolocationSerializer',
    )


class LinkedDeedJSONAPISerializer(BaseLinkedActivityJSONAPISerializer):
    class Meta(BaseLinkedActivityJSONAPISerializer.Meta):
        model = LinkedDeed
        fields = BaseLinkedActivityJSONAPISerializer.Meta.fields + ('start', 'end')
        read_only_fields = fields

    class JSONAPIMeta(BaseLinkedActivityJSONAPISerializer.JSONAPIMeta):
        resource_name = 'activities/deed-links'


class LinkedCollectCampaignJSONAPISerializer(LinkedActivityWithLocationJSONAPISerializer):
    class Meta(LinkedActivityWithLocationJSONAPISerializer.Meta):
        model = LinkedCollectCampaign
        fields = LinkedActivityWithLocationJSONAPISerializer.Meta.fields + (
            'location_hint', 'collect_type', 'start', 'end'
        )
        read_only_fields = fields

    class JSONAPIMeta(LinkedActivityWithLocationJSONAPISerializer.JSONAPIMeta):
        resource_name = 'activities/collect-links'


class LinkedFundingJSONAPISerializer(LinkedActivityWithLocationJSONAPISerializer):
    target = MoneySerializer(read_only=True)
    amount_raised = MoneySerializer(read_only=True, source='donated')

    class Meta(LinkedActivityWithLocationJSONAPISerializer.Meta):
        model = LinkedFunding
        fields = LinkedActivityWithLocationJSONAPISerializer.Meta.fields + ('target', 'amount_raised')
        read_only_fields = fields

    class JSONAPIMeta(LinkedActivityWithLocationJSONAPISerializer.JSONAPIMeta):
        resource_name = 'activities/funding-links'


class LinkedGrantApplicationJSONAPISerializer(LinkedActivityWithLocationJSONAPISerializer):
    target = MoneySerializer(read_only=True)

    class Meta(LinkedActivityWithLocationJSONAPISerializer.Meta):
        model = LinkedGrantApplication
        fields = LinkedActivityWithLocationJSONAPISerializer.Meta.fields + ('target',)
        read_only_fields = fields

    class JSONAPIMeta(LinkedActivityWithLocationJSONAPISerializer.JSONAPIMeta):
        resource_name = 'activities/grant-application-links'


class LinkedDeadlineActivityJSONAPISerializer(LinkedActivityWithLocationJSONAPISerializer):
    deadline = LocalDateField(source='end', allow_null=True)

    class Meta(LinkedActivityWithLocationJSONAPISerializer.Meta):
        model = LinkedDeadlineActivity
        fields = LinkedActivityWithLocationJSONAPISerializer.Meta.fields + ('duration', 'start', 'deadline')
        read_only_fields = fields

    class JSONAPIMeta(LinkedActivityWithLocationJSONAPISerializer.JSONAPIMeta):
        resource_name = 'activities/deadline-links'


class LinkedPeriodicActivityJSONAPISerializer(LinkedActivityWithLocationJSONAPISerializer):
    deadline = LocalDateField(source='end', allow_null=True)

    class Meta(LinkedActivityWithLocationJSONAPISerializer.Meta):
        model = LinkedPeriodicActivity
        fields = LinkedActivityWithLocationJSONAPISerializer.Meta.fields + ('duration', 'period', 'start', 'deadline')
        read_only_fields = fields

    class JSONAPIMeta(LinkedActivityWithLocationJSONAPISerializer.JSONAPIMeta):
        resource_name = 'activities/periodic-links'


class LinkedScheduleActivityJSONAPISerializer(LinkedActivityWithLocationJSONAPISerializer):
    deadline = LocalDateField(source='end', allow_null=True)

    class Meta(LinkedActivityWithLocationJSONAPISerializer.Meta):
        model = LinkedScheduleActivity
        fields = LinkedActivityWithLocationJSONAPISerializer.Meta.fields + ('duration', 'start', 'deadline')
        read_only_fields = fields

    class JSONAPIMeta(LinkedActivityWithLocationJSONAPISerializer.JSONAPIMeta):
        resource_name = 'activities/schedule-links'


class LinkedDateSlotJSONAPISerializer(json_api_serializers.ModelSerializer):
    location = ResourceRelatedField(read_only=True)
    duration = serializers.DurationField(read_only=True)

    class Meta:
        model = LinkedDateSlot
        fields = ('id', 'start', 'end', 'duration', 'location')
        read_only_fields = fields

    class JSONAPIMeta:
        resource_name = 'activities/date-link-slots'
        included_resources = ['location']

    included_serializers = {
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
    }


class LinkedDateActivityJSONAPISerializer(BaseLinkedActivityJSONAPISerializer):
    slots = ResourceRelatedField(many=True, read_only=True)
    slot_count = serializers.SerializerMethodField()
    date_info = serializers.SerializerMethodField()

    def get_sorted_slots(self, obj, only_upcoming=False):
        slots = sorted(
            (slot for slot in obj.slots.all() if slot.start),
            key=lambda slot: slot.start
        )
        if only_upcoming:
            slots = [slot for slot in slots if slot.start >= now()]

        return slots

    def get_slot_count(self, obj):
        upcoming = self.get_sorted_slots(obj, only_upcoming=True)
        if upcoming:
            return len(upcoming)
        # Past activities: fall back to all slots.
        return len(self.get_sorted_slots(obj))

    def get_date_info(self, obj):
        all_slots = self.get_sorted_slots(obj)
        slots = self.get_sorted_slots(obj, only_upcoming=True)
        total = len(all_slots)
        end = max((slot.end for slot in all_slots if slot.end), default=None)
        duration = None

        if total > 1:
            count = len(slots)
            first = slots[0].start.date() if slots else None
            end = end.date() if end else None
        elif total == 1:
            slot = all_slots[0]
            first = slot.start
            duration = slot.duration
            count = 1
        else:
            first = None
            count = 0

        # Linked slots have no capacity, so capacity and spots left are unknown
        return {
            'total': total,
            'has_multiple': total > 1,
            'is_full': False,
            'count': count,
            'first': first,
            'end': end,
            'duration': duration,
            'capacity': None,
            'spots_left': None,
        }

    class Meta(BaseLinkedActivityJSONAPISerializer.Meta):
        model = LinkedDateActivity
        fields = BaseLinkedActivityJSONAPISerializer.Meta.fields + ('slots', 'slot_count', 'date_info')
        read_only_fields = fields

    class JSONAPIMeta(BaseLinkedActivityJSONAPISerializer.JSONAPIMeta):
        resource_name = 'activities/date-links'
        included_resources = BaseLinkedActivityJSONAPISerializer.JSONAPIMeta.included_resources + [
            'slots', 'slots.location'
        ]

    included_serializers = dict(
        BaseLinkedActivityJSONAPISerializer.included_serializers,
        **{
            'slots': 'bluebottle.activity_links.serializers.LinkedDateSlotJSONAPISerializer',
            'slots.location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )
