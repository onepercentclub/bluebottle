from bluebottle.geo.models import Geolocation
from django.db import models, connection
from django.urls import reverse
from isodate import parse_duration
from rest_framework import serializers, exceptions
from rest_polymorphic.serializers import PolymorphicSerializer

from bluebottle.activity_pub.fields import IdField, RelatedActivityPubField, TypeField
from bluebottle.activity_pub.models import (
    Accept,
    Announce,
    Event,
    Follow,
    Inbox,
    Outbox,
    Person,
    Place,
    PublicKey,
    Publish,
    Organization,
    Actor,
    Activity
)
from bluebottle.activity_pub.utils import is_local, timedelta_to_iso
from bluebottle.deeds.models import Deed
from bluebottle.files.serializers import ORIGINAL_SIZE
from bluebottle.time_based.models import DeadlineActivity, DateActivity, DateActivitySlot, ActivitySlot
from bluebottle.utils.fields import RichTextField


class ActivityPubSerializer(serializers.ModelSerializer):
    type = TypeField()
    id = IdField(source="*", required=False)

    class Meta:
        exclude = ('polymorphic_ctype', 'url')

    def get_url_name(self, instance):
        return self.Meta.url_name

    def to_internal_value(self, data):
        result = super().to_internal_value(data)

        if 'id' in data and not is_local(data['id']):
            result['url'] = data['id']

        return result


class PolymorphicActivityPubSerializerMetaclass(serializers.SerializerMetaclass):
    def __new__(cls, *args, **kwargs):
        result = super().__new__(cls, *args, **kwargs)
        if hasattr(result, 'polymorphic_serializers'):
            for serializer in result.polymorphic_serializers:
                if not issubclass(serializer.Meta.model, result.Meta.model):
                    raise TypeError(f'{serializer.Meta.model} is not a subclass of {result.Meta.model}')

        return result


class PolymorphicActivityPubSerializer(
    serializers.Serializer, metaclass=PolymorphicActivityPubSerializerMetaclass
):
    def __init__(self, *args, **kwargs):
        self._serializers = [
            serializer(*args, **kwargs) for serializer in self.polymorphic_serializers
        ]
        super().__init__(*args, **kwargs)

    def get_url_name(self, instance):
        return self.get_serializer(instance).Meta.url_name

    def get_serializer(self, data):
        if isinstance(data, models.Model):
            for serializer in self._serializers:
                if serializer.Meta.model == data.__class__:
                    return serializer

            raise TypeError(f'Incompatible serializers for type: {type(data)}')
        else:
            if 'type' not in data:
                raise exceptions.ValidationError({'type': 'This field is required'})

            for serializer in self._serializers:
                if data['type'] == serializer.Meta.type:
                    return serializer

            raise exceptions.ValidationError(f'No serializer found for type: {data["type"]}')

    def to_representation(self, instance):
        return self.get_serializer(instance).to_representation(instance)

    def to_internal_value(self, data):
        return self.get_serializer(data).to_internal_value(data)

    def save(self, *args, **kwargs):
        return self.get_serializer(self.initial_data).save(*args, **kwargs)

    def create(self, validated_data):
        return self.get_serializer(self.initial_data).create(validated_data)

    def update(self, instance, validated_data):
        return self.get_serializer(instance).update(validated_data)

    def is_valid(self, *args, **kwargs):
        super().is_valid(*args, **kwargs)

        model_classes = [serializer.Meta.model for serializer in self._serializers]

        if self.instance and type(self.instance) not in model_classes:
            raise TypeError(f'Incompatible serializers for type: {type(self.instance)}')

        serializer = self.get_serializer(self.initial_data)

        return serializer.is_valid(*args, **kwargs)


class InboxSerializer(ActivityPubSerializer):
    class Meta(ActivityPubSerializer.Meta):
        type = 'Inbox'
        model = Inbox
        url_name = 'json-ld:inbox'


class OutboxSerializer(ActivityPubSerializer):
    class Meta(ActivityPubSerializer.Meta):
        type = 'Outbox'
        url_name = 'json-ld:outbox'
        model = Outbox


class PublicKeySerializer(ActivityPubSerializer):
    public_key_pem = serializers.CharField(allow_blank=True)

    class Meta(ActivityPubSerializer.Meta):
        type = 'PublicKey'
        url_name = 'json-ld:public-key'
        model = PublicKey
        exclude = ActivityPubSerializer.Meta.exclude + ('private_key', )


class PersonSerializer(ActivityPubSerializer):
    inbox = RelatedActivityPubField(InboxSerializer)
    outbox = RelatedActivityPubField(OutboxSerializer)
    public_key = RelatedActivityPubField(PublicKeySerializer, include=True)

    class Meta(ActivityPubSerializer.Meta):
        type = 'Person'
        url_name = 'json-ld:person'
        exclude = ActivityPubSerializer.Meta.exclude + ('member', )
        model = Person


class OrganizationSerializer(ActivityPubSerializer):
    inbox = RelatedActivityPubField(InboxSerializer)
    outbox = RelatedActivityPubField(OutboxSerializer)
    public_key = RelatedActivityPubField(PublicKeySerializer, include=True)
    name = serializers.CharField()
    summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    image = serializers.URLField(required=False, allow_blank=True, allow_null=True)

    class Meta(ActivityPubSerializer.Meta):
        type = 'Organization'
        url_name = 'json-ld:organization'
        exclude = ActivityPubSerializer.Meta.exclude + ('organization', )
        model = Organization


class ActorSerializer(PolymorphicActivityPubSerializer):
    polymorphic_serializers = [
        OrganizationSerializer, PersonSerializer
    ]

    class Meta:
        model = Actor


class DurationField(serializers.DurationField):
    def to_representation(self, value):
        return timedelta_to_iso(value) if value else None

    def to_internal_value(self, data):
        return parse_duration(data)


class PlaceSerializer(ActivityPubSerializer):
    name = serializers.CharField()
    latitude = serializers.DecimalField(max_digits=10, decimal_places=6, coerce_to_string=False)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=6, coerce_to_string=False)

    address = serializers.SerializerMethodField()

    geo = serializers.SerializerMethodField()

    locality = serializers.CharField()
    region = serializers.CharField()
    country = serializers.CharField()
    country_code = serializers.CharField()
    identifier = serializers.SerializerMethodField()

    class Meta(ActivityPubSerializer.Meta):
        type = 'Place'
        url_name = 'json-ld:place'
        model = Place

    def get_address(self, obj):
        """Return Schema.org PostalAddress structure"""
        return {
            "type": "PostalAddress",
            "streetAddress": obj.street_address,
            "addressLocality": obj.locality,
            "addressRegion": obj.region,
            "postalCode": obj.postal_code,
            "addressCountry": obj.country_code
        }

    def get_geo(self, obj):
        """Return Schema.org GeoCoordinates structure"""
        try:
            latitude = float(obj.latitude) if obj.latitude else None
            longitude = float(obj.longitude) if obj.longitude else None
        except (ValueError, TypeError):
            latitude = longitude = None

        return {
            "type": "GeoCoordinates",
            "latitude": latitude,
            "longitude": longitude
        }

    def get_identifier(self, obj):
        """Return identifier array with mapbox ID if available"""
        identifiers = []
        if obj.mapbox_id:
            identifiers.append({
                "scheme": "mapbox",
                "value": obj.mapbox_id
            })
        return identifiers if identifiers else None

    def to_representation(self, instance):
        """Override to add custom context information for Place objects"""
        data = super().to_representation(instance)
        data['_custom_context'] = 'place_with_schema'
        data = {k: v for k, v in data.items() if v is not None}

        return data

    def create(self, validated_data):
        data = validated_data.copy()
        data.pop('url', None)
        data.pop('id', None)
        data.pop('type', None)
        data.pop('identifier', None)
        data.pop('https://schema.org/postal_address', None)
        data.pop('https://schema.org/geo', None)
        place = Place.objects.create(**data)
        return place


class EventSerializer(ActivityPubSerializer):
    organizer = RelatedActivityPubField(OrganizationSerializer)
    start = serializers.DateTimeField(required=False)
    end = serializers.DateTimeField(required=False)
    name = serializers.CharField()
    description = serializers.CharField()
    duration = DurationField(required=False)
    sub_event = serializers.SerializerMethodField()
    place = PlaceSerializer(required=False, read_only=True)

    def get_sub_event(self, obj):
        subevents = obj.subevents.all().order_by("start")
        if subevents.exists():
            return EventSerializer(subevents, many=True, context=self.context).data
        return None

    def create(self, validated_data):
        place_data = validated_data.pop('place', None)
        instance = super().create(validated_data)

        if place_data:
            place_data.pop('url', None)
            place_data.pop('id', None)
            place_data.pop('type', None)
            place_data.pop('identifier', None)

            place = Place.objects.create(**place_data)
            instance.place = place
            instance.save()

        return instance

    class Meta(ActivityPubSerializer.Meta):
        type = 'Event'
        url_name = 'json-ld:event'
        exclude = ActivityPubSerializer.Meta.exclude + ('activity', 'slot_id')
        model = Event


class BaseActivitySerializer(ActivityPubSerializer):
    actor = RelatedActivityPubField(ActorSerializer)


class FollowSerializer(BaseActivitySerializer):
    object = RelatedActivityPubField(OrganizationSerializer)

    class Meta(ActivityPubSerializer.Meta):
        type = 'Follow'
        url_name = 'json-ld:follow'
        model = Follow


class AcceptSerializer(BaseActivitySerializer):
    object = RelatedActivityPubField(FollowSerializer)

    class Meta(ActivityPubSerializer.Meta):
        type = 'Accept'
        url_name = 'json-ld:accept'
        model = Accept


class PublishSerializer(BaseActivitySerializer):
    object = RelatedActivityPubField(EventSerializer)

    class Meta(ActivityPubSerializer.Meta):
        type = 'Publish'
        url_name = 'json-ld:publish'
        model = Publish


class AnnounceSerializer(BaseActivitySerializer):
    object = RelatedActivityPubField(EventSerializer)

    class Meta(ActivityPubSerializer.Meta):
        type = 'Announce'
        url_name = 'json-ld:announce'
        model = Announce


class ActivitySerializer(PolymorphicActivityPubSerializer):
    polymorphic_serializers = [
        FollowSerializer, AcceptSerializer, PublishSerializer, AnnounceSerializer
    ]

    class Meta:
        model = Activity


def download_event_image(event, user):
    from io import BytesIO

    import requests
    from django.core.files import File

    from bluebottle.files.models import Image

    if getattr(event, "image", None):
        try:
            response = requests.get(event.image, timeout=30)
            response.raise_for_status()

            image = Image(owner=user)
            import time

            filename = f"event_{event.pk}_{int(time.time())}.jpg"
            image.file.save(filename, File(BytesIO(response.content)))
            return image
        except Exception:
            return None
    return None


def get_absolute_path(tenant, path):
    return tenant.build_absolute_url(path) if (tenant and path) else None


class PlaceEventSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    name = serializers.CharField(source='locality')
    street_0address = serializers.SerializerMethodField()
    postal_code = serializers.CharField()
    locality = serializers.CharField()
    region = serializers.CharField(source='province')
    country = serializers.CharField(source='country.name')
    country_code = serializers.CharField(source='country.alpha2_code')
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    mapbox_id = serializers.CharField()

    def get_type(self, obj):
        return 'Place'

    def get_street_address(self, obj):
        parts = []
        if obj.street:
            parts.append(obj.street)
        if obj.street_number:
            parts.append(obj.street_number)
        return ' '.join(parts) if parts else None

    def get_latitude(self, obj):
        return str(obj.position.y) if obj.position else None

    def get_longitude(self, obj):
        return str(obj.position.x) if obj.position else None

    def to_representation(self, instance):
        """Override to add custom context information for Place objects"""
        data = super().to_representation(instance)
        data['_custom_context'] = 'place_with_schema'
        return data

    class Meta:
        model = Geolocation
        fields = [
            'type',
            'name',
            'street_address',
            'postal_code',
            'locality',
            'region',
            'country',
            'country_code',
            'latitude',
            'longitude',
            'mapbox_id'
        ]


class BaseActivityEventSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='title', required=False)
    description = RichTextField(required=False, allow_null=True)
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        image_url = None
        if obj.image:
            image_url = get_absolute_path(
                connection.tenant,
                reverse('activity-image', args=(str(obj.pk), ORIGINAL_SIZE))
            )
        elif obj.initiative and obj.initiative.image:
            image_url = get_absolute_path(
                connection.tenant,
                reverse('initiative-image', args=(str(obj.initiative.pk), ORIGINAL_SIZE))
            )
        return image_url

    def save(self, **kwargs):
        # Get user from kwargs (passed from view) or from context
        user = kwargs.get('owner') or (
            self.context.get('request') and self.context['request'].user
        )

        # Call parent save first to create/update the activity
        activity = super().save(**kwargs)

        # Check if there's an image URL in the initial data and we have a user
        if (
            hasattr(self, 'initial_data') and
            self.initial_data.get('image') and
            user and
            not activity.image
        ):  # Only download if no image is already set

            # Create a mock event object with the image URL for download_event_image
            class MockEvent:
                def __init__(self, image_url, pk):
                    self.image = image_url
                    self.pk = pk

            mock_event = MockEvent(self.initial_data['image'], activity.pk)
            downloaded_image = download_event_image(mock_event, user)

            if downloaded_image:
                activity.image = downloaded_image
                activity.save()

        return activity

    class Meta:
        model = Activity
        fields = ('name', 'description', 'image')


class DateToDateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        from datetime import datetime, time, date
        from django.utils import timezone

        if not value:
            return None

        if isinstance(value, date) and not isinstance(value, datetime):
            value = datetime.combine(value, time(12, 0))

        # Ensure timezone-aware
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())

        return value.isoformat()


class DeedEventSerializer(BaseActivityEventSerializer):
    start = DateToDateTimeField(required=False, allow_null=True)
    end = DateToDateTimeField(required=False, allow_null=True)

    class Meta:
        model = Deed
        fields = BaseActivityEventSerializer.Meta.fields + ('start', 'end')


class DeadlineActivityEventSerializer(BaseActivityEventSerializer):
    start = DateToDateTimeField(required=False, allow_null=True)
    end = DateToDateTimeField(source='deadline', required=False, allow_null=True)
    duration = serializers.DurationField(required=False, allow_null=True)
    place = PlaceEventSerializer(source='location', required=False, allow_null=True)

    class Meta:
        model = DeadlineActivity
        fields = BaseActivityEventSerializer.Meta.fields + ('duration', 'start', 'end', 'place')


class BaseSlotEventSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='title', required=False)
    start = serializers.DateTimeField(required=False, allow_null=True)
    end = serializers.DateTimeField(required=False, allow_null=True)
    place = PlaceEventSerializer(source='location', required=False, allow_null=True)

    class Meta:
        model = ActivitySlot
        fields = ('name', 'start', 'end', 'place')


class DateActivitySlotEventSerializer(BaseSlotEventSerializer):

    class Meta:
        model = DateActivitySlot
        fields = BaseSlotEventSerializer.Meta.fields


class DateActivityEventSerializer(BaseActivityEventSerializer):
    subevents = DateActivitySlotEventSerializer(
        source='slots',
        required=False,
        allow_null=True,
        allow_empty=True,
        many=True
    )

    class Meta:
        model = DateActivity
        fields = BaseActivityEventSerializer.Meta.fields + ('subevents',)


class ActivityEventSerializer(PolymorphicSerializer):

    polymorphic_serializers = [
        DeedEventSerializer,
        DeadlineActivityEventSerializer,
        DateActivityEventSerializer,
    ]

    model_serializer_mapping = {
        Deed: DeedEventSerializer,
        DeadlineActivity: DeadlineActivityEventSerializer,
        DateActivity: DateActivityEventSerializer
    }

    def get_serializer_from_data(self, data):
        if 'subevents' in data:
            return DateActivityEventSerializer
        elif 'duration' in data:
            return DeadlineActivityEventSerializer
        else:
            return DeedEventSerializer

    def to_internal_value(self, data):
        serializer = self.get_serializer_from_data(data)
        result = serializer().to_internal_value(data)
        return result

    def create(self, validated_data):
        validated_data.pop('resourcetype', None)
        serializer = self.get_serializer_from_data(validated_data)
        return serializer().create(validated_data)
