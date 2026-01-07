from rest_framework import serializers

from bluebottle.activity_pub.models import (
    Accept,
    Announce,
    CrowdFunding,
    Address,
    Place,
    Follow,
    Inbox,
    Outbox,
    Person,
    PublicKey,
    Publish,
    Update,
    Organization,
    Actor,
    Activity,
    GoodDeed,
    Image,
    Event,
    DoGoodEvent,
    SubEvent,
)
from bluebottle.activity_pub.serializers.base import (
    ActivityPubSerializer, PolymorphicActivityPubSerializer
)
from bluebottle.activity_pub.serializers.fields import ActivityPubIdField, TypeField


class InboxSerializer(ActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:inbox')
    type = TypeField('Inbox')

    class Meta(ActivityPubSerializer.Meta):
        model = Inbox


class OutboxSerializer(ActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:outbox')
    type = TypeField('Outbox')

    class Meta(ActivityPubSerializer.Meta):
        model = Outbox


class PublicKeySerializer(ActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:public-key')
    type = TypeField('PublicKey')
    public_key_pem = serializers.CharField(allow_blank=True)

    class Meta(ActivityPubSerializer.Meta):
        model = PublicKey
        fields = ActivityPubSerializer.Meta.fields + ('public_key_pem',)


class PersonSerializer(ActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:person')
    type = TypeField('Person')
    inbox = InboxSerializer()
    outbox = OutboxSerializer()
    public_key = PublicKeySerializer(include=True)

    class Meta(ActivityPubSerializer.Meta):
        fields = ActivityPubSerializer.Meta.fields + ('inbox', 'outbox', 'public_key', 'name')
        model = Person


class ImageSerializer(ActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:image')
    type = TypeField('Image')
    url = serializers.URLField()
    name = serializers.CharField(allow_null=True, allow_blank=True)

    class Meta(ActivityPubSerializer.Meta):
        model = Image
        fields = ActivityPubSerializer.Meta.fields + ('url', 'name', )


class OrganizationSerializer(ActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:organization')
    type = TypeField('Organization')
    inbox = InboxSerializer(required=False, allow_null=True)
    outbox = OutboxSerializer(required=False, allow_null=True)
    public_key = PublicKeySerializer(include=True, required=False, allow_null=True)
    name = serializers.CharField()
    summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    logo = ImageSerializer(required=False, allow_null=True)

    class Meta(ActivityPubSerializer.Meta):
        fields = ActivityPubSerializer.Meta.fields + (
            'inbox', 'outbox', 'public_key', 'name', 'summary', 'content', 'image', 'logo'
        )
        model = Organization


class ActorSerializer(PolymorphicActivityPubSerializer):
    polymorphic_serializers = [
        OrganizationSerializer, PersonSerializer
    ]

    class Meta:
        model = Actor


class AddressSerializer(ActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:address')
    type = TypeField('Address')

    street_address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    address_locality = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    address_region = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    address_country = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta(ActivityPubSerializer.Meta):
        model = Address
        fields = ActivityPubSerializer.Meta.fields + (
            'street_address', 'postal_code', 'address_locality', 'address_region', 'address_country',
        )


class PlaceSerializer(ActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:place')
    type = TypeField('Place')

    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    name = serializers.CharField()

    address = AddressSerializer(allow_null=True, include=True, required=False)

    class Meta(ActivityPubSerializer.Meta):
        model = Place
        fields = ActivityPubSerializer.Meta.fields + ('latitude', 'longitude', 'name', 'address', )


class BaseEventSerializer(ActivityPubSerializer):
    name = serializers.CharField()
    summary = serializers.CharField()
    image = ImageSerializer(include=True, allow_null=True, required=False)
    organization = OrganizationSerializer(include=True, allow_null=True, required=False)
    url = serializers.URLField()

    class Meta(ActivityPubSerializer.Meta):
        fields = ActivityPubSerializer.Meta.fields + (
            'name', 'summary', 'image', 'organization', 'url',
        )


class GoodDeedSerializer(BaseEventSerializer):
    id = ActivityPubIdField(url_name='json-ld:good-deed')
    type = TypeField('GoodDeed')

    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)

    class Meta(BaseEventSerializer.Meta):
        model = GoodDeed
        fields = BaseEventSerializer.Meta.fields + ('start_time', 'end_time')


class CrowdFundingSerializer(BaseEventSerializer):
    id = ActivityPubIdField(url_name='json-ld:crowd-funding')
    type = TypeField('CrowdFunding')

    end_time = serializers.DateTimeField(required=False, allow_null=True)
    start_time = serializers.DateTimeField(required=False, allow_null=True)

    target = serializers.DecimalField(decimal_places=2, max_digits=10)
    target_currency = serializers.CharField()
    donated = serializers.DecimalField(decimal_places=2, max_digits=10)
    donated_currency = serializers.CharField()

    location = PlaceSerializer(allow_null=True, include=True, required=False)

    class Meta(BaseEventSerializer.Meta):
        model = CrowdFunding
        fields = BaseEventSerializer.Meta.fields + (
            'end_time', 'start_time',
            'target', 'target_currency',
            'donated', 'donated_currency',
            'location'
        )


class SubEventSerializer(ActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:sub-event')
    type = TypeField('Event')

    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)

    location = PlaceSerializer(allow_null=True, include=True, required=False)
    event_attendance_mode = serializers.ChoiceField(
        choices=['OnlineEventAttendanceMode', 'OfflineEventAttendanceMode']
    )
    duration = serializers.DurationField(required=False, allow_null=True)

    class Meta(BaseEventSerializer.Meta):
        model = SubEvent
        fields = ActivityPubSerializer.Meta.fields + (
            'location', 'start_time', 'end_time', 'duration', 'event_attendance_mode',
        )


class DoGoodEventSerializer(BaseEventSerializer):
    id = ActivityPubIdField(url_name='json-ld:do-good-event')
    type = TypeField('DoGoodEvent')

    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    registration_deadline = serializers.DateTimeField(required=False, allow_null=True)

    location = PlaceSerializer(allow_null=True, include=True, required=False)
    event_attendance_mode = serializers.ChoiceField(
        choices=['OnlineEventAttendanceMode', 'OfflineEventAttendanceMode'],
        required=False,
        allow_null=True
    )
    join_mode = serializers.ChoiceField(
        choices=['OpenJoinMode', 'ReviewJoinMode'],
        required=False,
        allow_null=True
    )
    duration = serializers.DurationField(required=False, allow_null=True)

    sub_event = SubEventSerializer(many=True, allow_null=True, required=False)

    class Meta(BaseEventSerializer.Meta):
        model = DoGoodEvent
        fields = BaseEventSerializer.Meta.fields + (
            'location', 'start_time', 'end_time', 'duration',
            'event_attendance_mode', 'join_mode', 'registration_deadline',
            'sub_event',
        )

    def create(self, validated_data):
        sub_events = validated_data.pop('sub_event', [])
        result = super().create(validated_data)
        field = self.fields['sub_event']
        field.initial_data = sub_events

        field.is_valid(raise_exception=True)
        field.save(parent=result)
        return result

    def update(self, instance, validated_data):
        sub_events = validated_data.pop('sub_event', [])
        result = super().update(instance, validated_data)

        field = self.fields['sub_event']
        field.initial_data = sub_events

        field.is_valid(raise_exception=True)
        field.save(parent=result)

        return result


class EventSerializer(PolymorphicActivityPubSerializer):
    polymorphic_serializers = [
        GoodDeedSerializer, CrowdFundingSerializer, DoGoodEventSerializer
    ]

    class Meta:
        model = Event


class BaseActivitySerializer(ActivityPubSerializer):
    actor = ActorSerializer()

    class Meta(ActivityPubSerializer.Meta):
        fields = ActivityPubSerializer.Meta.fields + ('actor', 'object')


class FollowSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:follow')
    type = TypeField('Follow')
    object = ActorSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Follow


class AcceptSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:accept')
    type = TypeField('Accept')

    object = FollowSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Accept


class PublishSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:publish')
    type = TypeField('Publish')
    object = EventSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Publish


class UpdateSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:update')
    type = TypeField('Update')
    object = EventSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Update


class AnnounceSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:announce')
    type = TypeField('Announce')
    object = EventSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Announce


class ActivitySerializer(PolymorphicActivityPubSerializer):
    polymorphic_serializers = [
        FollowSerializer, AcceptSerializer, PublishSerializer,
        AnnounceSerializer, UpdateSerializer
    ]

    class Meta:
        model = Activity
