from django.db import models
from django.urls import reverse
from isodate import parse_duration
from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer

from bluebottle.activities.models import Activity
from bluebottle.activity_pub.fields import IdField, RelatedActivityPubField, TypeField
from bluebottle.activity_pub.models import (
    Accept,
    Announce,
    Event,
    Follow,
    Inbox,
    Outbox,
    Person,
    PublicKey,
    Publish,
    PubOrganization,
)
from bluebottle.activity_pub.utils import is_local, timedelta_to_iso
import json

from bluebottle.deeds.models import Deed
from bluebottle.files.serializers import ORIGINAL_SIZE
from bluebottle.time_based.models import DeadlineActivity, DateActivity, DateActivitySlot, ActivitySlot
from bluebottle.utils.fields import RichTextField


class ActivityPubSerializer(serializers.ModelSerializer):
    type = TypeField()
    id = IdField(source="*")

    class Meta:
        exclude = ('polymorphic_ctype', 'url')

    def save(self, **kwargs):
        if not is_local(self.initial_data['id']):
            try:
                self.instance = self.Meta.model.objects.get(url=self.initial_data['id'])
            except self.Meta.model.DoesNotExist:
                pass
        return super().save(**kwargs)

    def to_internal_value(self, data):
        result = super().to_internal_value(data)

        if not is_local(data['id']):
            result['url'] = data['id']

        return result


class PolymorphicActivityPubSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        self._serializers = [
            serializer(*args, **kwargs) for serializer in self.polymorphic_serializers
        ]
        super().__init__(*args, **kwargs)

    def get_serializer(self, data):
        if isinstance(data, models.Model):
            for serializer in self._serializers:
                if serializer.Meta.model == data.__class__:
                    return serializer
        else:
            for serializer in self._serializers:
                if data['type'] == serializer.Meta.type:
                    return serializer

    def to_representation(self, instance):
        return self.get_serializer(instance).to_representation(instance)

    def to_internal_value(self, data):
        return self.get_serializer(data).to_internal_value(data)

    def create(self, validated_data):
        return self.get_serializer(self.initial_data).create(validated_data)

    def update(self, instance, validated_data):
        return self.get_serializer(instance).update(validated_data)

    def is_valid(self, *args, **kwargs):
        super().is_valid(*args, **kwargs)

        if hasattr(self, 'instance') and self.instance:
            serializer = self.get_serializer(self.instance)
        else:
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
        model = PubOrganization


class DurationField(serializers.DurationField):
    def to_representation(self, value):
        return timedelta_to_iso(value) if value else None

    def to_internal_value(self, data):
        return parse_duration(data)


class EventSerializer(ActivityPubSerializer):
    organizer = RelatedActivityPubField(OrganizationSerializer)
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)
    name = serializers.CharField()
    description = serializers.CharField()
    duration = DurationField(required=False)
    gu_activity_type = serializers.SerializerMethodField()
    sub_event = serializers.SerializerMethodField()

    def get_gu_activity_type(self, obj):
        return str(obj.activity.__class__.__name__)

    def get_sub_event(self, obj):
        subevents = obj.subevents.all().order_by("start")
        if subevents.exists():
            return EventSerializer(subevents, many=True, context=self.context).data
        return None

    class Meta(ActivityPubSerializer.Meta):
        type = 'Event'
        url_name = 'json-ld:event'
        exclude = ActivityPubSerializer.Meta.exclude + ('activity', 'slot_id')
        model = Event


class BaseActivitySerializer(ActivityPubSerializer):
    actor = RelatedActivityPubField(OrganizationSerializer)


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


def _download_event_image(event, user):
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


class BaseActivityEventSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='title', required=False)
    description = RichTextField(required=False, allow_null=True)
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        image_url = None
        if obj.image:
            image_url = reverse('activity-image', args=(str(obj.pk), ORIGINAL_SIZE))
        elif obj.initiative and obj.initiative.image:
            image_url = reverse('initiative-image', args=(str(obj.initiative.pk), ORIGINAL_SIZE))
        return image_url

    class Meta:
        model = Activity
        fields = ('name', 'description')


class DeedEventSerializer(BaseActivityEventSerializer):
    start = serializers.DateField(source='start', required=False, allow_null=True)
    end = serializers.DateField(source='end', required=False, allow_null=True)

    class Meta:
        model = Deed
        fields = BaseActivityEventSerializer.Meta.fields + ('start', 'end')


class DeadlineActivityEventSerializer(BaseActivityEventSerializer):
    start = serializers.DateField(source='start', required=False, allow_null=True)
    end = serializers.DateField(source='deadline', required=False, allow_null=True)
    duration = serializers.DurationField(required=False, allow_null=True)

    class Meta:
        model = DeadlineActivity
        fields = BaseActivityEventSerializer.Meta.fields + ('duration', 'start', 'end')


class BaseSlotEventSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='title', required=False)
    start = serializers.DateTimeField(required=False, allow_null=True)
    end = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = ActivitySlot
        fields = ('name', 'start', 'end')


class DateActivitySlotEventSerializer(BaseSlotEventSerializer):

    class Meta:
        model = DateActivitySlot
        fields = BaseSlotEventSerializer.Meta.fields


class DateActivityEventSerializer(BaseActivityEventSerializer):
    subevents = DateActivitySlotEventSerializer(
        source='slots',
        required=False,
        allow_null=True,
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
    