from bluebottle.activity_pub.serializers.base import ActivityPubSerializer, PolymorphicActivityPubSerializer
from rest_framework import serializers

from bluebottle.activity_pub.serializers.fields import IdField
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
    Activity,
    GoodDeed,
    Image
)


class InboxSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:inbox')

    class Meta(ActivityPubSerializer.Meta):
        type = 'Inbox'
        model = Inbox


class OutboxSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:outbox')
    class Meta(ActivityPubSerializer.Meta):
        type = 'Outbox'
        model = Outbox


class PublicKeySerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:public-key')
    public_key_pem = serializers.CharField(allow_blank=True)

    class Meta(ActivityPubSerializer.Meta):
        type = 'PublicKey'
        model = PublicKey
        exclude = ActivityPubSerializer.Meta.exclude + ('private_key',)


class PersonSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:person')
    inbox = InboxSerializer()
    outbox = OutboxSerializer()
    public_key = PublicKeySerializer(include=True)

    class Meta(ActivityPubSerializer.Meta):
        type = 'Person'
        exclude = ActivityPubSerializer.Meta.exclude + ('member',)
        model = Person


class OrganizationSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:organization')
    inbox = InboxSerializer()
    outbox = OutboxSerializer()
    public_key = PublicKeySerializer(include=True)
    name = serializers.CharField()
    summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    image = serializers.URLField(required=False, allow_blank=True, allow_null=True)

    class Meta(ActivityPubSerializer.Meta):
        type = 'Organization'
        exclude = ActivityPubSerializer.Meta.exclude + ('organization',)
        model = Organization


class ActorSerializer(PolymorphicActivityPubSerializer):
    polymorphic_serializers = [
        OrganizationSerializer, PersonSerializer
    ]

    class Meta:
        model = Actor


class ImageSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:image')
    url = serializers.URLField()
    name = serializers.CharField()

    class Meta(ActivityPubSerializer.Meta):
        type = 'Image'
        model = Image


class GoodDeedSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:good-deed')

    startTime = serializers.DateField(required=False, allow_null=True)
    endTime = serializers.DateField(required=False, allow_null=True)
    name = serializers.CharField()
    summary = serializers.CharField()
    image = ImageSerializer(include=True, allow_null=True)

    class Meta(ActivityPubSerializer.Meta):
        type = 'GoodDeed'
        exclude = ActivityPubSerializer.Meta.exclude + ('activity', )
        model = GoodDeed


class BaseActivitySerializer(ActivityPubSerializer):
    actor = OrganizationSerializer()


class FollowSerializer(BaseActivitySerializer):
    id = IdField(url_name='json-ld:follow')
    object = OrganizationSerializer()

    class Meta(ActivityPubSerializer.Meta):
        type = 'Follow'
        model = Follow


class AcceptSerializer(BaseActivitySerializer):
    id = IdField(url_name='json-ld:accept')

    object = FollowSerializer()

    class Meta(ActivityPubSerializer.Meta):
        type = 'Accept'
        model = Accept


class PublishSerializer(BaseActivitySerializer):
    id = IdField(url_name='json-ld:publish')
    object = GoodDeedSerializer()

    class Meta(ActivityPubSerializer.Meta):
        type = 'Publish'
        model = Publish


class AnnounceSerializer(BaseActivitySerializer):
    id = IdField(url_name='json-ld:announce')
    object = GoodDeedSerializer()

    class Meta(ActivityPubSerializer.Meta):
        type = 'Announce'
        model = Announce


class ActivitySerializer(PolymorphicActivityPubSerializer):
    polymorphic_serializers = [
        FollowSerializer, AcceptSerializer, PublishSerializer, AnnounceSerializer
    ]

    class Meta:
        model = Activity