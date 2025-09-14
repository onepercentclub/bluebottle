from django.db import models
from isodate import parse_duration
from rest_framework import serializers

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
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    name = serializers.CharField()
    description = serializers.CharField()
    duration = DurationField(required=False)
    gu_activity_type = serializers.SerializerMethodField()
    sub_event = serializers.SerializerMethodField()

    def get_gu_activity_type(self, obj):
        return str(obj.activity.__class__.__name__)
        return obj.activity.__class__.__name__

    def get_sub_event(self, obj):
        subevents = obj.subevents.all().order_by("start_date")
        if subevents.exists():
            return EventSerializer(subevents, many=True, context=self.context).data
        return None

    class Meta(ActivityPubSerializer.Meta):
        type = 'Event'
        url_name = 'json-ld:event'
        exclude = ActivityPubSerializer.Meta.exclude + ('activity', )
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
