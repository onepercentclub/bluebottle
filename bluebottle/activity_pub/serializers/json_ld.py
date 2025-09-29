from bluebottle.activity_pub.serializers.base import (
    ActivityPubSerializer, PolymorphicActivityPubSerializer
)
from rest_framework import serializers

from bluebottle.activity_pub.serializers.fields import IdField, TypeField
from bluebottle.activity_pub.models import (
    Accept,
    Announce,
    CrowdFunding,
    CollectionDrive,
    Follow,
    Inbox,
    Outbox,
    Person,
    PublicKey,
    Publish,
    Organization,
    Actor,
    Activity,
    GoodDeed,
    Image,
    Event
)


class InboxSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:inbox')
    type = TypeField('Inbox')

    class Meta(ActivityPubSerializer.Meta):
        model = Inbox


class OutboxSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:outbox')
    type = TypeField('Outbox')

    class Meta(ActivityPubSerializer.Meta):
        model = Outbox


class PublicKeySerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:public-key')
    type = TypeField('PublicKey')
    public_key_pem = serializers.CharField(allow_blank=True)

    class Meta(ActivityPubSerializer.Meta):
        model = PublicKey
        exclude = ActivityPubSerializer.Meta.exclude + ('private_key',)


class PersonSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:person')
    type = TypeField('Person')
    inbox = InboxSerializer()
    outbox = OutboxSerializer()
    public_key = PublicKeySerializer(include=True)

    class Meta(ActivityPubSerializer.Meta):
        exclude = ActivityPubSerializer.Meta.exclude + ('member',)
        model = Person


class OrganizationSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:organization')
    type = TypeField('Organization')
    inbox = InboxSerializer()
    outbox = OutboxSerializer()
    public_key = PublicKeySerializer(include=True)
    name = serializers.CharField()
    summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    image = serializers.URLField(required=False, allow_blank=True, allow_null=True)

    class Meta(ActivityPubSerializer.Meta):
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
    type = TypeField('Image')
    url = serializers.URLField()
    name = serializers.CharField()

    class Meta(ActivityPubSerializer.Meta):
        model = Image


class BaseEventSerializer(ActivityPubSerializer):
    name = serializers.CharField()
    summary = serializers.CharField()
    image = ImageSerializer(include=True)

    class Meta(ActivityPubSerializer.Meta):
        exclude = ActivityPubSerializer.Meta.exclude + ('activity', )


class GoodDeedSerializer(BaseEventSerializer):
    id = IdField(url_name='json-ld:good-deed')
    type = TypeField('GoodDeed')

    startTime = serializers.DateField(required=False)
    endTime = serializers.DateField(required=False)

    class Meta(ActivityPubSerializer.Meta):
        model = GoodDeed


class CrowdFundingSerializer(BaseEventSerializer):
    id = IdField(url_name='json-ld:crowd-funding')
    type = TypeField('CrowdFunding')

    endTime = serializers.DateField(required=False)

    target = serializers.DecimalField(decimal_places=2, max_digits=10)
    realized = serializers.DecimalField(decimal_places=2, max_digits=10)

    currencty = serializers.CharField(required=False)

    class Meta(ActivityPubSerializer.Meta):
        model = CrowdFunding


class CollectionDriveSerializer(BaseEventSerializer):
    id = IdField(url_name='json-ld:collection-drive')
    type = TypeField('CollectionDrive')

    startTime = serializers.DateField(required=False)
    endTime = serializers.DateField(required=False)

    class Meta(ActivityPubSerializer.Meta):
        model = CollectionDrive


class EventSerializer(PolymorphicActivityPubSerializer):
    polymorphic_serializers = [
        GoodDeedSerializer, CollectionDriveSerializer, CrowdFundingSerializer
    ]

    class Meta:
        model = Event


class BaseActivitySerializer(ActivityPubSerializer):
    actor = ActorSerializer()


class FollowSerializer(BaseActivitySerializer):
    id = IdField(url_name='json-ld:follow')
    type = TypeField('Follow')
    object = ActorSerializer()

    class Meta(ActivityPubSerializer.Meta):
        model = Follow


class AcceptSerializer(BaseActivitySerializer):
    id = IdField(url_name='json-ld:accept')
    type = TypeField('Accept')

    object = FollowSerializer()

    class Meta(ActivityPubSerializer.Meta):
        model = Accept


class PublishSerializer(BaseActivitySerializer):
    id = IdField(url_name='json-ld:publish')
    type = TypeField('Publish')
    object = GoodDeedSerializer()

    class Meta(ActivityPubSerializer.Meta):
        model = Publish


class AnnounceSerializer(BaseActivitySerializer):
    id = IdField(url_name='json-ld:announce')
    type = TypeField('Announce')
    object = GoodDeedSerializer()

    class Meta(ActivityPubSerializer.Meta):
        model = Announce


class ActivitySerializer(PolymorphicActivityPubSerializer):
    polymorphic_serializers = [
        FollowSerializer, AcceptSerializer, PublishSerializer, AnnounceSerializer
    ]

    class Meta:
        model = Activity
