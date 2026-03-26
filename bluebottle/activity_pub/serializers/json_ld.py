from rest_framework import serializers

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models import (
    Accept,
    ActivityPubModel,
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
    Start,
    Cancel,
    Finish,
    Join,
    Leave,
    Organization,
    Actor,
    Activity,
    GoodDeed,
    Image,
    Event,
    DoGoodEvent,
    SubEvent,
    GrantApplication,
)
from bluebottle.activity_pub.serializers.base import (
    ActivityPubListSerializer,
    ActivityPubSerializer,
    PolymorphicActivityPubSerializer,
)
from bluebottle.activity_pub.serializers.fields import ActivityPubIdField, TypeField
from bluebottle.activity_pub.utils import is_local


class SubEventListSerializer(ActivityPubListSerializer):
    def save(self, **kwargs):
        validated_data = [
            {**attrs, **kwargs} for attrs in self.validated_data
        ]
        parent = kwargs.get('parent')
        if parent is None:
            raise ValueError('SubEventListSerializer.save() requires parent=<DoGoodEvent>')

        incoming_pks = []
        for item in validated_data:
            raw_id = item.get('id')
            sub = SubEvent.objects.from_iri(raw_id) if raw_id else None
            if sub is not None and sub.parent_id == parent.pk:
                incoming_pks.append(self.child.update(sub, item).pk)
            else:
                incoming_pks.append(self.child.create(item).pk)

        for orphan in parent.sub_event.exclude(pk__in=incoming_pks):
            orphan.delete()

        return list(parent.sub_event.order_by('start_time', 'id'))


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
    contributor_count = serializers.IntegerField(
        required=False, allow_null=True, default=0
    )

    class Meta(BaseEventSerializer.Meta):
        model = GoodDeed
        fields = BaseEventSerializer.Meta.fields + (
            'start_time', 'end_time', 'contributor_count'
        )


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


class GrantApplicationSerializer(BaseEventSerializer):
    id = ActivityPubIdField(url_name='json-ld:grant-application')
    type = TypeField('GrantApplication')

    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    target = serializers.DecimalField(decimal_places=2, max_digits=10, required=False, allow_null=True)
    target_currency = serializers.CharField(required=False, allow_null=True)
    location = PlaceSerializer(allow_null=True, include=True, required=False)

    class Meta(BaseEventSerializer.Meta):
        model = GrantApplication
        fields = BaseEventSerializer.Meta.fields + (
            'end_time', 'start_time',
            'target', 'target_currency',
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

    name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)

    location = PlaceSerializer(allow_null=True, include=True, required=False)
    event_attendance_mode = serializers.ChoiceField(
        choices=['OnlineEventAttendanceMode', 'OfflineEventAttendanceMode'],
        required=False,
        allow_null=True,
    )
    duration = serializers.DurationField(required=False, allow_null=True)
    contributor_count = serializers.IntegerField(required=False, allow_null=True, default=0)
    capacity = serializers.IntegerField(required=False, allow_null=True)

    class Meta(BaseEventSerializer.Meta):
        model = SubEvent
        list_serializer_class = SubEventListSerializer
        fields = ActivityPubSerializer.Meta.fields + (
            'name', 'location', 'start_time', 'end_time', 'duration', 'event_attendance_mode',
            'contributor_count', 'capacity',
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
    contributor_count = serializers.IntegerField(required=False, allow_null=True, default=0)
    capacity = serializers.IntegerField(required=False, allow_null=True)

    sub_event = SubEventSerializer(many=True, allow_null=True, required=False, include=True)

    class Meta(BaseEventSerializer.Meta):
        model = DoGoodEvent
        fields = BaseEventSerializer.Meta.fields + (
            'location', 'start_time', 'end_time', 'duration',
            'event_attendance_mode', 'join_mode',
            'repetition_mode', 'slot_mode',
            'application_deadline',
            'contributor_count',
            'capacity',
            'sub_event',
        )

    def create(self, validated_data):
        has_sub_events = 'sub_event' in validated_data
        sub_events = validated_data.pop('sub_event') if has_sub_events else None
        result = super().create(validated_data)
        if has_sub_events:
            field = self.fields['sub_event']
            field.initial_data = sub_events if sub_events is not None else []
            field.is_valid(raise_exception=True)
            field.save(parent=result)
        return result

    def update(self, instance, validated_data):
        has_sub_events = 'sub_event' in validated_data
        sub_events = validated_data.pop('sub_event') if has_sub_events else None
        result = super().update(instance, validated_data)
        if has_sub_events:
            field = self.fields['sub_event']
            field.initial_data = sub_events if sub_events is not None else []
            field.is_valid(raise_exception=True)
            field.save(parent=result)
        return result


class EventSerializer(PolymorphicActivityPubSerializer):
    polymorphic_serializers = [
        GoodDeedSerializer,
        CrowdFundingSerializer,
        GrantApplicationSerializer,
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
    adoption_type = serializers.ChoiceField(
        choices=['link', 'clone', 'sync'],
        required=False,
        allow_null=True
    )

    class Meta(BaseActivitySerializer.Meta):
        model = Follow
        fields = BaseActivitySerializer.Meta.fields + ('adoption_type', )


class EventOrFollowSerializer(EventSerializer):
    polymorphic_serializers = EventSerializer.polymorphic_serializers + [
        FollowSerializer,
    ]

    class Meta(EventSerializer.Meta):
        model = ActivityPubModel


class AcceptObjectSerializer(PolymorphicActivityPubSerializer):
    """Accept.object can be a Follow (Activity) or an Event (e.g. CrowdFunding)."""
    polymorphic_serializers = [
        FollowSerializer,
        EventSerializer,
        GoodDeedSerializer,
        CrowdFundingSerializer,
        GrantApplicationSerializer,
        CollectCampaignSerializer,
        DoGoodEventSerializer,
    ]

    class Meta:
        model = ActivityPubModel


class AcceptSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:accept')
    type = TypeField('Accept')

    object = AcceptObjectSerializer()

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
    object = EventOrFollowSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Update

    def save(self, *args, **kwargs):
        if 'object' in self.validated_data and isinstance(self.validated_data['object'], dict):
            object_id = self.validated_data['object'].get('id')
            if object_id:
                if is_local(object_id):
                    self.validated_data['object'] = ActivityPubModel.objects.from_iri(object_id)
                else:
                    self.validated_data['object'] = adapter.fetch(object_id)
                    # Allow nested EventSerializer to apply the update when we have fetched data
                    self.context['internal_update'] = True
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


class StartSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:start')
    type = TypeField('Start')
    object = EventSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Start


class FinishSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:finish')
    type = TypeField('Finish')
    object = EventSerializer()

    class Meta(BaseActivitySerializer.Meta):
        model = Finish


class JoinSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:join')
    type = TypeField('Join')
    object = EventSerializer()
    sub_event = SubEventSerializer(required=False, allow_null=True, include=True)
    participant_sync_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    participant_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    participant_email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)

    class Meta(BaseActivitySerializer.Meta):
        model = Join
        fields = BaseActivitySerializer.Meta.fields + (
            'sub_event',
            'participant_sync_id', 'participant_name', 'participant_email',
        )

    def save(self, *args, **kwargs):
        if 'object' in self.validated_data and isinstance(self.validated_data['object'], dict):
            object_id = self.validated_data['object'].get('id')
            if object_id:
                if is_local(object_id):
                    self.validated_data['object'] = Event.objects.from_iri(object_id)
                else:
                    self.validated_data['object'] = adapter.fetch(object_id)
        if 'sub_event' in self.validated_data and isinstance(self.validated_data['sub_event'], dict):
            sub_id = self.validated_data['sub_event'].get('id')
            if sub_id:
                if is_local(sub_id):
                    self.validated_data['sub_event'] = SubEvent.objects.from_iri(sub_id)
                else:
                    self.validated_data['sub_event'] = adapter.fetch(sub_id)
        return super().save(*args, **kwargs)


class LeaveSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:leave')
    type = TypeField('Leave')
    object = EventSerializer()
    sub_event = SubEventSerializer(required=False, allow_null=True, include=True)
    participant_sync_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta(BaseActivitySerializer.Meta):
        model = Leave
        fields = BaseActivitySerializer.Meta.fields + ('sub_event', 'participant_sync_id',)

    def save(self, *args, **kwargs):
        if 'object' in self.validated_data and isinstance(self.validated_data['object'], dict):
            object_id = self.validated_data['object'].get('id')
            if object_id:
                if is_local(object_id):
                    self.validated_data['object'] = Event.objects.from_iri(object_id)
                else:
                    self.validated_data['object'] = adapter.fetch(object_id)
        if 'sub_event' in self.validated_data and isinstance(self.validated_data['sub_event'], dict):
            sub_id = self.validated_data['sub_event'].get('id')
            if sub_id:
                if is_local(sub_id):
                    self.validated_data['sub_event'] = SubEvent.objects.from_iri(sub_id)
                else:
                    self.validated_data['sub_event'] = adapter.fetch(sub_id)
        return super().save(*args, **kwargs)


class ActivitySerializer(PolymorphicActivityPubSerializer):
    polymorphic_serializers = [
        FollowSerializer,
        AcceptSerializer,
        CreateSerializer,
        UpdateSerializer,
        StartSerializer,
        CancelSerializer,
        DeleteSerializer,
        FinishSerializer,
        JoinSerializer,
        LeaveSerializer,
    ]

    class Meta:
        model = Activity
