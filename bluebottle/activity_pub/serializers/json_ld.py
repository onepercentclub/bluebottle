from rest_framework import serializers, exceptions

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models import (
    Accept,
    CrowdFunding,
    CollectCampaign,
    Address,
    Place,
    Follow,
    Inbox,
    Outbox,
    Person,
    PublicKey,
    Create,
    Update,
    Delete,
    Cancel,
    Finish,
    Organization,
    Actor,
    Activity,
    GoodDeed,
    Image,
    Document,
    Collection,
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
    type = TypeField('inbox')

    class Meta(ActivityPubSerializer.Meta):
        model = Inbox


class OutboxSerializer(ActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:outbox')
    type = TypeField('outbox')

    class Meta(ActivityPubSerializer.Meta):
        model = Outbox


class PublicKeySerializer(ActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:public-key')
    type = TypeField('publicKey')
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
    name = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta(ActivityPubSerializer.Meta):
        model = Image
        fields = ActivityPubSerializer.Meta.fields + ('url', 'name', )

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except exceptions.ParseError:
            return super().to_internal_value({
                'id': data['id'],
                'type': 'Image',
                'url': data['id']
            })


class DocumentSerializer(ActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:document')
    type = TypeField('Document')
    url = serializers.URLField()
    name = serializers.CharField(allow_null=True, allow_blank=True)
    summary = serializers.CharField(allow_null=True, allow_blank=True)
    icon = ImageSerializer(required=False, allow_null=True)

    class Meta(ActivityPubSerializer.Meta):
        model = Document
        fields = ActivityPubSerializer.Meta.fields + ('url', 'name', 'summary', 'icon')


class CollectionSerializer(ActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:collection')
    type = TypeField('Collection')
    name = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    summary = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    items = DocumentSerializer(many=True, required=False)

    class Meta(ActivityPubSerializer.Meta):
        model = Collection
        fields = ActivityPubSerializer.Meta.fields + ('name', 'summary', 'items')

    def save(self, **kwargs):
        items = self.validated_data.pop('items')

        instance = super().save()

        self.validated_data['items'] = items

        self.fields['items'].initial_data = items
        self.fields['items'].is_valid(raise_exception=True)
        self.fields['items'].save(part_of=instance)

        return instance


class OrganizationSerializer(ActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:organization')
    type = TypeField('Organization')
    inbox = InboxSerializer(required=False, allow_null=True)
    outbox = OutboxSerializer(required=False, allow_null=True)
    public_key = PublicKeySerializer(include=True, required=False, allow_null=True)
    name = serializers.CharField()
    summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    icon = ImageSerializer(required=False, allow_null=True)

    class Meta(ActivityPubSerializer.Meta):
        fields = ActivityPubSerializer.Meta.fields + (
            'inbox', 'outbox', 'public_key', 'name', 'summary', 'content', 'image', 'icon'
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

    summary = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    street_address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    locality = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    region = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    country = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta(ActivityPubSerializer.Meta):
        model = Address
        fields = ActivityPubSerializer.Meta.fields + (
            'street_address', 'postal_code', 'locality', 'region', 'country', 'summary'
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
    summary = serializers.CharField(allow_null=True, allow_blank=True, required=False)
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


class CollectCampaignSerializer(BaseEventSerializer):
    id = ActivityPubIdField(url_name='json-ld:collect-campaign')
    type = TypeField('CollectCampaign')

    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    location = PlaceSerializer(allow_null=True, include=True, required=False)
    collect_type = serializers.CharField(required=False, allow_null=True)
    target = serializers.FloatField(required=False, allow_null=True)
    donated = serializers.FloatField(required=False, allow_null=True)

    class Meta(BaseEventSerializer.Meta):
        model = CollectCampaign
        fields = BaseEventSerializer.Meta.fields + (
            'start_time', 'end_time', 'location', 'collect_type', 'target', 'donated'
        )


class SubEventSerializer(ActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:sub-event')
    type = TypeField('Event')

    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)

    location = PlaceSerializer(allow_null=True, include=True, required=False)
    event_attendance_mode = serializers.ChoiceField(
        choices=['OnlineEventAttendanceMode', 'OfflineEventAttendanceMode'],
        required=False,
        allow_null=True,
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
    application_deadline = serializers.DateTimeField(required=False, allow_null=True)

    location = PlaceSerializer(allow_null=True, include=True, required=False)
    event_attendance_mode = serializers.ChoiceField(
        choices=['OnlineEventAttendanceMode', 'OfflineEventAttendanceMode'],
        required=False,
        allow_null=True
    )
    join_mode = serializers.ChoiceField(
        choices=['OpenJoinMode', 'ReviewJoinMode', 'SelectedJoinMode', 'ScheduleJoinMode'],
        required=False,
        allow_null=True
    )
    repetition_mode = serializers.ChoiceField(
        choices=['DailyRepetitionMode', 'WeeklyRepetitionMode', 'MonthlyRepetitionMode', 'OnceRepetitionMode'],
        required=False,
        allow_null=True
    )
    slot_mode = serializers.ChoiceField(
        choices=['PeriodicSlotMode', 'ScheduledSlotMode', 'SetSlotMode'],
        required=False,
        allow_null=True
    )

    duration = serializers.DurationField(required=False, allow_null=True)

    sub_event = SubEventSerializer(many=True, allow_null=True, required=False, include=True)

    class Meta(BaseEventSerializer.Meta):
        model = DoGoodEvent
        fields = BaseEventSerializer.Meta.fields + (
            'location', 'start_time', 'end_time', 'duration',
            'event_attendance_mode', 'join_mode',
            'repetition_mode', 'slot_mode',
            'application_deadline',
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
        GoodDeedSerializer,
        CrowdFundingSerializer,
        CollectCampaignSerializer,
        DoGoodEventSerializer,
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


class CreateSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:create')
    type = TypeField('Create')
    object = EventSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Create


class UpdateSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:update')
    type = TypeField('Update')
    object = EventSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Update

    def save(self, *args, **kwargs):
        self.validated_data['object'] = adapter.fetch(self.validated_data['object']['id'])
        return super().save(*args, **kwargs)


class DeleteSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:delete')
    type = TypeField('Delete')
    object = EventSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Delete


class CancelSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:cancel')
    type = TypeField('Cancel')
    object = EventSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Cancel


class FinishSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:finish')
    type = TypeField('Finish')
    object = EventSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Finish


class ActivitySerializer(PolymorphicActivityPubSerializer):
    polymorphic_serializers = [
        FollowSerializer, AcceptSerializer, CreateSerializer,
        UpdateSerializer, CancelSerializer,
        DeleteSerializer, FinishSerializer
    ]

    class Meta:
        model = Activity
