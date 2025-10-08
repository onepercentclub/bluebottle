from bluebottle.activity_pub.serializers.base import (
    ActivityPubSerializer, PolymorphicActivityPubSerializer
)
from rest_framework import serializers

from bluebottle.activity_pub.serializers.fields import IdField, TypeField
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
    Organization,
    Actor,
    Activity,
    GoodDeed,
    Image,
    Event,
    DoGoodEvent,
    SubEvent,
)


class InboxSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:inbox')
    type = TypeField('Inbox')

    class Meta(ActivityPubSerializer.Meta):
        model = Inbox


class OutboxSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:outbox')
    type = TypeField('OrderedCollection')

    class Meta(ActivityPubSerializer.Meta):
        model = Outbox

    def to_representation(self, data):
        result = super().to_representation(data)
        if self.parent:
            return result
        else:
            view = self.context['view']
            request = self.context['request']

            pagination = view.pagination_class()
            pagination.paginate_queryset(
                view.page_view(request=request, kwargs=view.kwargs).get_queryset(),
                self.context['request'],
                view
            )

            result['totalItems'] = pagination.page.paginator.count
            result['first'] = pagination.get_link(1)
            result['last'] = pagination.get_link(pagination.page.paginator.num_pages)

            return result


class PublicKeySerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:public-key')
    type = TypeField('PublicKey')
    public_key_pem = serializers.CharField(allow_blank=True)

    class Meta(ActivityPubSerializer.Meta):
        model = PublicKey
        fields = ActivityPubSerializer.Meta.fields + ('public_key_pem',)


class FollowersSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:followers')
    type = TypeField('OrderedCollection')

    class Meta(ActivityPubSerializer.Meta):
        model = Inbox


class BaseActorSerializer(ActivityPubSerializer):
    inbox = InboxSerializer()
    outbox = OutboxSerializer()
    public_key = PublicKeySerializer(include=True)
    followers = PublicKeySerializer(include=True)

    class Meta(ActivityPubSerializer.Meta):
        fields = ActivityPubSerializer.Meta.fields + ('inbox', 'outbox', 'public_key', 'name')
        model = Person


class PersonSerializer(BaseActorSerializer):
    id = IdField(url_name='json-ld:person')
    type = TypeField('Person')

    class Meta(BaseActorSerializer.Meta):
        model = Person


class OrganizationSerializer(BaseActorSerializer):
    id = IdField(url_name='json-ld:organization')
    type = TypeField('Organization')

    name = serializers.CharField()
    summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    image = serializers.URLField(required=False, allow_blank=True, allow_null=True)

    class Meta(BaseActorSerializer.Meta):
        fields = BaseActorSerializer.Meta.fields + (
            'name', 'summary', 'content', 'image',
        )
        model = Organization


class ActorSerializer(PolymorphicActivityPubSerializer):
    polymorphic_serializers = [
        OrganizationSerializer, PersonSerializer
    ]

    class Meta(PolymorphicActivityPubSerializer.Meta):
        model = Actor


class ImageSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:image')
    type = TypeField('Image')
    url = serializers.URLField()
    name = serializers.CharField()

    class Meta(ActivityPubSerializer.Meta):
        model = Image
        fields = ActivityPubSerializer.Meta.fields + ('url', 'name', )


class AddressSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:address')
    type = TypeField('Address')

    street_address = serializers.CharField(required=False, allow_null=True)
    postal_code = serializers.CharField(required=False, allow_null=True)

    address_locality = serializers.CharField(required=False, allow_null=True)
    address_region = serializers.CharField(required=False, allow_null=True)
    address_country = serializers.CharField(required=False, allow_null=True)

    class Meta(ActivityPubSerializer.Meta):
        model = Address
        fields = ActivityPubSerializer.Meta.fields + (
            'street_address', 'postal_code', 'address_locality', 'address_region', 'address_country',
        )


class PlaceSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:place')
    type = TypeField('Place')

    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    name = serializers.CharField()

    address = AddressSerializer(allow_null=True, include=True)

    class Meta(ActivityPubSerializer.Meta):
        model = Place
        fields = ActivityPubSerializer.Meta.fields + ('latitude', 'longitude', 'name', 'address', )


class BaseEventSerializer(ActivityPubSerializer):
    name = serializers.CharField()
    summary = serializers.CharField()
    image = ImageSerializer(include=True, allow_null=True)

    class Meta(ActivityPubSerializer.Meta):
        fields = ActivityPubSerializer.Meta.fields + ('name', 'summary', 'image', )


class GoodDeedSerializer(BaseEventSerializer):
    id = IdField(url_name='json-ld:good-deed')
    type = TypeField('GoodDeed')

    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)

    class Meta(BaseEventSerializer.Meta):
        model = GoodDeed
        fields = BaseEventSerializer.Meta.fields + ('start_time', 'end_time', )


class CrowdFundingSerializer(BaseEventSerializer):
    id = IdField(url_name='json-ld:crowd-funding')
    type = TypeField('CrowdFunding')

    end_time = serializers.DateTimeField(required=False, allow_null=True)

    target = serializers.DecimalField(decimal_places=2, max_digits=10)
    target_currency = serializers.CharField()

    location = PlaceSerializer(allow_null=True, include=True, required=False)

    class Meta(BaseEventSerializer.Meta):
        model = CrowdFunding
        fields = BaseEventSerializer.Meta.fields + ('end_time', 'target', 'target_currency', 'location')


class SubEventSerializer(ActivityPubSerializer):
    id = IdField(url_name='json-ld:sub-event')
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
    id = IdField(url_name='json-ld:do-good-event')
    type = TypeField('DoGoodEvent')

    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)

    location = PlaceSerializer(allow_null=True, include=True, required=False)
    event_attendance_mode = serializers.ChoiceField(
        choices=['OnlineEventAttendanceMode', 'OfflineEventAttendanceMode'],
        required=False,
        allow_null=True
    )
    duration = serializers.DurationField(required=False, allow_null=True)

    sub_events = SubEventSerializer(many=True, allow_null=True, required=False)

    class Meta(BaseEventSerializer.Meta):
        model = DoGoodEvent
        fields = BaseEventSerializer.Meta.fields + (
            'location', 'start_time', 'end_time', 'duration', 'event_attendance_mode', 'sub_events'
        )

    def create(self, validated_data):
        sub_events = validated_data.pop('sub_events', [])
        result = super().create(validated_data)

        field = self.fields['sub_events']
        field.initial_data = sub_events

        field.is_valid(raise_exception=True)
        field.save(parent=result)

        return result


class EventSerializer(PolymorphicActivityPubSerializer):
    polymorphic_serializers = [
        GoodDeedSerializer, CrowdFundingSerializer, DoGoodEventSerializer
    ]

    class Meta(PolymorphicActivityPubSerializer.Meta):
        model = Event


class BaseActivitySerializer(ActivityPubSerializer):
    actor = ActorSerializer()

    class Meta(ActivityPubSerializer.Meta):
        model = Follow
        fields = ActivityPubSerializer.Meta.fields + ('actor', 'object')


class FollowSerializer(BaseActivitySerializer):
    id = IdField(url_name='json-ld:follow')
    type = TypeField('Follow')
    object = ActorSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Follow


class AcceptSerializer(BaseActivitySerializer):
    id = IdField(url_name='json-ld:accept')
    type = TypeField('Accept')

    object = FollowSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Accept


class PublishSerializer(BaseActivitySerializer):
    id = IdField(url_name='json-ld:publish')
    type = TypeField('Publish')
    object = EventSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Publish


class AnnounceSerializer(BaseActivitySerializer):
    id = IdField(url_name='json-ld:announce')
    type = TypeField('Announce')
    object = EventSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Announce


class ActivitySerializer(PolymorphicActivityPubSerializer):
    polymorphic_serializers = [
        FollowSerializer, AcceptSerializer, PublishSerializer, AnnounceSerializer
    ]

    class Meta(PolymorphicActivityPubSerializer.Meta):
        model = Activity
