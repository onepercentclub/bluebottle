from django.db import models
from rest_framework import serializers

from bluebottle.activity_pub.fields import IdField, RelatedActivityPubField, TypeField
from bluebottle.activity_pub.models import (
    Person, Inbox, Outbox, PublicKey, Follow, Accept, Event, Publish, Announce
)
from bluebottle.activity_pub.utils import is_local


class ActivityPubSerializer(serializers.ModelSerializer):
    type = TypeField()
    id = IdField(source="*")

    class Meta:
        exclude = ('polymorphic_ctype', 'url')

    def to_internal_value(self, data):
        result = super().to_internal_value(data)

        if not is_local(data['id']):
            result['url'] = data['id']

        return result


class PolymorpphicActivityPubSerializer(serializers.Serializer):
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


class EventSerializer(ActivityPubSerializer):
    organizer = RelatedActivityPubField(PersonSerializer)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    name = serializers.CharField()
    description = serializers.CharField()

    class Meta(ActivityPubSerializer.Meta):
        type = 'Event'
        url_name = 'json-ld:event'
        exclude = ActivityPubSerializer.Meta.exclude + ('activity', )
        model = Event


class BaseActivitySerializer(ActivityPubSerializer):
    actor = RelatedActivityPubField(PersonSerializer)


class FollowSerializer(BaseActivitySerializer):
    object = RelatedActivityPubField(PersonSerializer)

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


class ActivitySerializer(PolymorpphicActivityPubSerializer):
    polymorphic_serializers = [
        FollowSerializer, AcceptSerializer, PublishSerializer
    ]
