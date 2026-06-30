from rest_framework import serializers
from rest_framework.relations import RelatedField

from bluebottle.activity_pub.clients import client
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
    Reject,
    Update,
    Delete,
    Start,
    Cancel,
    Finish,
    Join,
    Leave,
    Organization,
    GoodDeed,
    Image,
    DoGoodEvent,
    SubEvent,
    GrantApplication,
)
from bluebottle.activity_pub.serializers.base import BaseActivityPubSerializer
from bluebottle.activity_pub.serializers.fields import TypeField
from bluebottle.activity_pub.serializers.relations import RelatedResourceField
from bluebottle.activity_pub.utils import is_local


class InboxSerializer(BaseActivityPubSerializer):
    type = TypeField('inbox')

    class Meta(BaseActivityPubSerializer.Meta):
        model = Inbox


class OutboxSerializer(BaseActivityPubSerializer):
    type = TypeField('outbox')

    class Meta(BaseActivityPubSerializer.Meta):
        model = Outbox


class PublicKeySerializer(BaseActivityPubSerializer):
    type = TypeField('publicKey')
    public_key_pem = serializers.CharField(allow_blank=True)

    class Meta(BaseActivityPubSerializer.Meta):
        model = PublicKey
        fields = BaseActivityPubSerializer.Meta.fields + ('public_key_pem',)


class PersonSerializer(BaseActivityPubSerializer):
    type = TypeField('Person')
    inbox = RelatedResourceField(type='inbox', required=False, allow_null=True)
    outbox = RelatedResourceField(type='outbox', required=False, allow_null=True)
    public_key = RelatedResourceField(type='publicKey', include=True, required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    given_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    family_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    email = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta(BaseActivityPubSerializer.Meta):
        fields = BaseActivityPubSerializer.Meta.fields + (
            'inbox', 'outbox', 'public_key', 'name', 'given_name', 'family_name', 'email'
        )
        model = Person

    def create(self, validated_data):
        if 'request' in self.context:
            validated_data['source'] = self.context['request'].auth

        return super().create(validated_data)


class ImageSerializer(BaseActivityPubSerializer):
    type = TypeField('Image')
    url = serializers.URLField()
    name = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta(BaseActivityPubSerializer.Meta):
        model = Image
        fields = BaseActivityPubSerializer.Meta.fields + ('url', 'name', )


class OrganizationSerializer(BaseActivityPubSerializer):
    type = TypeField('Organization')
    inbox = RelatedResourceField(type='inbox', required=False, allow_null=True)
    outbox = RelatedResourceField(type='outbox', required=False, allow_null=True)
    public_key = RelatedResourceField(type='publicKey', include=True, required=False, allow_null=True)
    name = serializers.CharField()
    summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    icon = RelatedResourceField(type='Image', required=False, allow_null=True)
    image = RelatedResourceField(type='Image', required=False, allow_null=True, include=True)
    preferred_username = serializers.CharField(required=False, allow_null=True)

    class Meta(BaseActivityPubSerializer.Meta):
        fields = BaseActivityPubSerializer.Meta.fields + (
            'inbox', 'outbox', 'public_key', 'name', 'summary', 'content',
            'image', 'icon', 'preferred_username'
        )
        model = Organization

    def create(self, validated_data):
        if 'request' in self.context:
            validated_data['source'] = self.context['request'].auth
        return super().create(validated_data)


class AddressSerializer(BaseActivityPubSerializer):
    type = TypeField('Address')

    summary = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    street_address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    locality = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    region = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    country = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta(BaseActivityPubSerializer.Meta):
        model = Address
        fields = BaseActivityPubSerializer.Meta.fields + (
            'street_address', 'postal_code', 'locality', 'region', 'country', 'summary'
        )


class PlaceSerializer(BaseActivityPubSerializer):
    type = TypeField('Place')

    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    name = serializers.CharField()

    address = RelatedResourceField(type='Address', allow_null=True, include=True, required=False)

    class Meta(BaseActivityPubSerializer.Meta):
        model = Place
        fields = BaseActivityPubSerializer.Meta.fields + ('latitude', 'longitude', 'name', 'address', )


class BaseEventSerializer(BaseActivityPubSerializer):
    name = serializers.CharField()
    summary = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    image = RelatedResourceField(type='Image', include=True, allow_null=True, required=False)
    organization = RelatedResourceField(type='Organization', include=True, allow_null=True, required=False)
    url = serializers.URLField()

    class Meta(BaseActivityPubSerializer.Meta):
        fields = BaseActivityPubSerializer.Meta.fields + (
            'name', 'summary', 'image', 'organization', 'url',
        )


class GoodDeedSerializer(BaseEventSerializer):
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
    type = TypeField('CrowdFunding')

    end_time = serializers.DateTimeField(required=False, allow_null=True)
    start_time = serializers.DateTimeField(required=False, allow_null=True)

    target = serializers.DecimalField(decimal_places=2, max_digits=10)
    target_currency = serializers.CharField()
    donated = serializers.DecimalField(decimal_places=2, max_digits=10)
    donated_currency = serializers.CharField()

    location = RelatedResourceField(type='Place', allow_null=True, include=True, required=False)

    class Meta(BaseEventSerializer.Meta):
        model = CrowdFunding
        fields = BaseEventSerializer.Meta.fields + (
            'end_time', 'start_time',
            'target', 'target_currency',
            'donated', 'donated_currency',
            'location'
        )


class GrantApplicationSerializer(BaseEventSerializer):
    type = TypeField('GrantApplication')

    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    target = serializers.DecimalField(decimal_places=2, max_digits=10, required=False, allow_null=True)
    target_currency = serializers.CharField(required=False, allow_null=True)
    location = RelatedResourceField(type='Place', allow_null=True, include=True, required=False)

    class Meta(BaseEventSerializer.Meta):
        model = GrantApplication
        fields = BaseEventSerializer.Meta.fields + (
            'end_time', 'start_time',
            'target', 'target_currency',
            'location'
        )


class CollectCampaignSerializer(BaseEventSerializer):
    type = TypeField('CollectCampaign')

    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    location = RelatedResourceField(type='Place', allow_null=True, include=True, required=False)
    collect_type = serializers.CharField(required=False, allow_null=True)
    target = serializers.FloatField(required=False, allow_null=True)
    donated = serializers.FloatField(required=False, allow_null=True)

    class Meta(BaseEventSerializer.Meta):
        model = CollectCampaign
        fields = BaseEventSerializer.Meta.fields + (
            'start_time', 'end_time', 'location', 'collect_type', 'target', 'donated'
        )


class RelatedParentField(RelatedField):
    def get_queryset(self):
        # TODO: filter queryset on correct types
        return DoGoodEvent.objects.all()

    def to_representation(self, value):
        return value.pub_url

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = {'id': data}

        return DoGoodEvent.objects.from_iri(data['id'])


class SubEventSerializer(BaseActivityPubSerializer):
    type = TypeField('subEvent')

    name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)

    location = RelatedResourceField(type='Place', allow_null=True, include=True, required=False)
    event_attendance_mode = serializers.ChoiceField(
        choices=['OnlineEventAttendanceMode', 'OfflineEventAttendanceMode'],
        required=False,
        allow_null=True,
    )
    duration = serializers.DurationField(required=False, allow_null=True)
    contributor_count = serializers.IntegerField(required=False, allow_null=True, default=0)
    capacity = serializers.IntegerField(required=False, allow_null=True)

    parent = RelatedParentField(allow_null=True)

    class Meta(BaseEventSerializer.Meta):
        model = SubEvent
        fields = BaseActivityPubSerializer.Meta.fields + (
            'location', 'start_time', 'end_time', 'duration', 'event_attendance_mode',
            'contributor_count', 'capacity', 'name', 'parent'
        )


class DoGoodEventSerializer(BaseEventSerializer):
    type = TypeField('DoGoodEvent')

    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    application_deadline = serializers.DateTimeField(required=False, allow_null=True)

    location = RelatedResourceField(type='Place', allow_null=True, include=True, required=False)
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

    sub_event = RelatedResourceField(type='SubEvent', many=True, allow_null=True, required=False, include=True)

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
        sub_events = validated_data.pop('sub_event', [])
        result = super().create(validated_data)
        field = self.fields['sub_event']

        if sub_events:
            for sub_event in sub_events:
                sub_event['parent'] = result
            sub_events = field.save(sub_events)

        return result


class BaseActivitySerializer(BaseActivityPubSerializer):
    actor = RelatedResourceField(type=('Organization', 'Person', ))

    class Meta(BaseActivityPubSerializer.Meta):
        fields = BaseActivityPubSerializer.Meta.fields + ('actor', 'object')


class FollowSerializer(BaseActivitySerializer):
    type = TypeField('Follow')
    object = RelatedResourceField(type=('Organization', 'Person', ))
    adoption_type = serializers.ChoiceField(
        choices=['link', 'clone', 'sync'],
        required=False,
        allow_null=True
    )

    class Meta(BaseActivitySerializer.Meta):
        model = Follow
        fields = BaseActivitySerializer.Meta.fields + ('adoption_type', )


class AcceptSerializer(BaseActivitySerializer):
    type = TypeField('Accept')

    object = RelatedResourceField(
        type=(
            'Follow', 'Event', 'GoodDeed', 'CrowdFunding', 'GrantApplication',
            'CollectCampaign', 'DoGoodEvent', 'Join'
        )
    )

    class Meta(BaseActivitySerializer.Meta):
        model = Accept


class RejectSerializer(BaseActivitySerializer):
    type = TypeField('Reject')

    object = RelatedResourceField(
        type=('Join', )
    )

    class Meta(BaseActivitySerializer.Meta):
        model = Reject


class CreateSerializer(BaseActivitySerializer):
    type = TypeField('Create')
    object = RelatedResourceField(
        type=(
            'Event', 'GoodDeed', 'CrowdFunding', 'GrantApplication',
            'CollectCampaign', 'DoGoodEvent'
        )
    )

    class Meta(BaseActivitySerializer.Meta):
        model = Create


class UpdateSerializer(BaseActivitySerializer):
    type = TypeField('Update')
    object = RelatedResourceField(
        type=(
            'Follow', 'Event', 'GoodDeed', 'CrowdFunding', 'GrantApplication',
            'CollectCampaign', 'DoGoodEvent'
        )
    )

    class Meta(BaseActivitySerializer.Meta):
        model = Update

    def to_internal_value(self, data):
        if isinstance(data['object'], str) and not is_local(data['object']):
            data['object'] = client.fetch(data['object'])

        return super().to_internal_value(data)


class DeleteSerializer(BaseActivitySerializer):
    type = TypeField('Delete')
    object = RelatedResourceField(
        type=(
            'Event', 'GoodDeed', 'CrowdFunding', 'GrantApplication',
            'CollectCampaign', 'DoGoodEvent'
        )
    )

    class Meta(BaseActivitySerializer.Meta):
        model = Delete


class CancelSerializer(BaseActivitySerializer):
    type = TypeField('Cancel')
    object = RelatedResourceField(
        type=(
            'Event', 'GoodDeed', 'CrowdFunding', 'GrantApplication',
            'CollectCampaign', 'DoGoodEvent'
        )
    )

    class Meta(BaseActivitySerializer.Meta):
        model = Cancel


class StartSerializer(BaseActivitySerializer):
    type = TypeField('Start')
    object = RelatedResourceField(
        type=(
            'Event', 'GoodDeed', 'CrowdFunding', 'GrantApplication',
            'CollectCampaign', 'DoGoodEvent'
        )
    )

    class Meta(BaseActivitySerializer.Meta):
        model = Start


class FinishSerializer(BaseActivitySerializer):
    type = TypeField('Finish')
    object = RelatedResourceField(
        type=(
            'Event', 'GoodDeed', 'CrowdFunding', 'GrantApplication',
            'CollectCampaign', 'DoGoodEvent'
        )
    )

    class Meta(BaseActivitySerializer.Meta):
        model = Finish


class JoinSerializer(BaseActivitySerializer):
    type = TypeField('Join')
    object = RelatedResourceField(
        type=(
            'Event', 'GoodDeed', 'CrowdFunding', 'GrantApplication',
            'CollectCampaign', 'DoGoodEvent', 'SubEvent'
        )
    )
    motivation = serializers.CharField(required=False, allow_null=True)

    class Meta(BaseActivitySerializer.Meta):
        model = Join
        fields = BaseActivitySerializer.Meta.fields + ('motivation', )

    def create(self, validated_data):
        if 'request' in self.context:
            validated_data['platform'] = self.context['request'].auth

        return super().create(validated_data)


class LeaveSerializer(BaseActivitySerializer):
    type = TypeField('Leave')
    object = RelatedResourceField(
        type=(
            'Event', 'GoodDeed', 'CrowdFunding', 'GrantApplication',
            'CollectCampaign', 'DoGoodEvent', 'SubEvent'
        )
    )

    class Meta(BaseActivitySerializer.Meta):
        model = Leave

    def save(self, *args, **kwargs):
        __import__('ipdb').set_trace()
        return super().save(*args, **kwargs)


from bluebottle.activity_pub.serializers.federated_activities import *  # noqa
