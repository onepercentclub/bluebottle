from rest_framework import serializers

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
    Start,
    Cancel,
    Finish,
    Organization,
    GoodDeed,
    Image,
    DoGoodEvent,
    SubEvent,
    GrantApplication,
)
from bluebottle.activity_pub.serializers.base import BaseActivityPubSerializer
from bluebottle.activity_pub.serializers.fields import (
    ActivityPubIdField, TypeField,
)
from bluebottle.activity_pub.serializers.relations import RelatedResourceField


class InboxSerializer(BaseActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:inbox')
    type = TypeField('inbox')

    class Meta(BaseActivityPubSerializer.Meta):
        model = Inbox


class OutboxSerializer(BaseActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:outbox')
    type = TypeField('outbox')

    class Meta(BaseActivityPubSerializer.Meta):
        model = Outbox


class PublicKeySerializer(BaseActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:public-key')
    type = TypeField('publicKey')
    public_key_pem = serializers.CharField(allow_blank=True)

    class Meta(BaseActivityPubSerializer.Meta):
        model = PublicKey
        fields = BaseActivityPubSerializer.Meta.fields + ('public_key_pem',)


class PersonSerializer(BaseActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:person')
    type = TypeField('Person')
    inbox = RelatedResourceField(type='inbox', required=False, allow_null=True)
    outbox = RelatedResourceField(type='outbox', required=False, allow_null=True)
    public_key = RelatedResourceField(type='publicKey', include=True, required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    given_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    family_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta(BaseActivityPubSerializer.Meta):
        fields = BaseActivityPubSerializer.Meta.fields + (
            'inbox', 'outbox', 'public_key', 'name', 'given_name', 'family_name',
        )
        model = Person


class ImageSerializer(BaseActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:image')
    type = TypeField('Image')
    url = serializers.URLField()
    name = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta(BaseActivityPubSerializer.Meta):
        model = Image
        fields = BaseActivityPubSerializer.Meta.fields + ('url', 'name', )


class OrganizationSerializer(BaseActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:organization')
    type = TypeField('Organization')
    inbox = RelatedResourceField(type='inbox', required=False, allow_null=True)
    outbox = RelatedResourceField(type='outbox', required=False, allow_null=True)
    public_key = RelatedResourceField(type='publicKey', include=True, required=False, allow_null=True)
    name = serializers.CharField()
    summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    icon = RelatedResourceField(type='Image', required=False, allow_null=True)
    image = RelatedResourceField(type='Image', required=False, allow_null=True, include=True)

    class Meta(BaseActivityPubSerializer.Meta):
        fields = BaseActivityPubSerializer.Meta.fields + (
            'inbox', 'outbox', 'public_key', 'name', 'summary', 'content', 'image', 'icon'
        )
        model = Organization


class AddressSerializer(BaseActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:address')
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
    id = ActivityPubIdField(url_name='json-ld:place')
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
    id = ActivityPubIdField(url_name='json-ld:grant-application')
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
    id = ActivityPubIdField(url_name='json-ld:collect-campaign')
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


class SubEventSerializer(BaseActivityPubSerializer):
    id = ActivityPubIdField(url_name='json-ld:sub-event')
    type = TypeField('subEvent')

    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)

    location = RelatedResourceField(type='Place', allow_null=True, include=True, required=False)
    event_attendance_mode = serializers.ChoiceField(
        choices=['OnlineEventAttendanceMode', 'OfflineEventAttendanceMode'],
        required=False,
        allow_null=True,
    )
    duration = serializers.DurationField(required=False, allow_null=True)

    class Meta(BaseEventSerializer.Meta):
        model = SubEvent
        fields = BaseActivityPubSerializer.Meta.fields + (
            'location', 'start_time', 'end_time', 'duration', 'event_attendance_mode',
        )


class DoGoodEventSerializer(BaseEventSerializer):
    id = ActivityPubIdField(url_name='json-ld:do-good-event')
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

    sub_event = RelatedResourceField(type='SubEvent', many=True, allow_null=True, required=False, include=True)

    class Meta(BaseEventSerializer.Meta):
        model = DoGoodEvent
        fields = BaseEventSerializer.Meta.fields + (
            'location', 'start_time', 'end_time', 'duration',
            'event_attendance_mode', 'join_mode',
            'repetition_mode', 'slot_mode',
            'application_deadline',
            'sub_event',
        )


class BaseActivitySerializer(BaseActivityPubSerializer):
    actor = RelatedResourceField(type=('Organization', 'Person', ))

    class Meta(BaseActivityPubSerializer.Meta):
        fields = BaseActivityPubSerializer.Meta.fields + ('actor', 'object')


class FollowSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:follow')
    type = TypeField('Follow')
    object = RelatedResourceField(type=('Organization', 'Person', ))
    adoption_type = serializers.ChoiceField(
        choices=['link', 'template'],
        required=False,
        allow_null=True
    )

    class Meta(BaseActivitySerializer.Meta):
        model = Follow
        fields = BaseActivitySerializer.Meta.fields + ('adoption_type', )


class AcceptSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:accept')
    type = TypeField('Accept')

    object = RelatedResourceField(
        type=(
            'Follow', 'Event', 'GoodDeed', 'CrowdFunding', 'GrantApplication',
            'CollectCampaign', 'DoGoodEvent'
        )
    )

    class Meta(BaseActivitySerializer.Meta):
        model = Accept


class CreateSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:create')
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
    id = ActivityPubIdField(url_name='json-ld:update')
    type = TypeField('Update')
    object = RelatedResourceField(
        type=(
            'Follow', 'Event', 'GoodDeed', 'CrowdFunding', 'GrantApplication',
            'CollectCampaign', 'DoGoodEvent'
        )
    )

    class Meta(BaseActivitySerializer.Meta):
        model = Update

    def save(self, *args, **kwargs):
        self.validated_data['object'] = adapter.fetch(self.validated_data['object']['id'])
        return super().save(*args, **kwargs)


class DeleteSerializer(BaseActivitySerializer):
    id = ActivityPubIdField(url_name='json-ld:delete')
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
    id = ActivityPubIdField(url_name='json-ld:cancel')
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
    id = ActivityPubIdField(url_name='json-ld:start')
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
    id = ActivityPubIdField(url_name='json-ld:finish')
    type = TypeField('Finish')
    object = RelatedResourceField(
        type=(
            'Event', 'GoodDeed', 'CrowdFunding', 'GrantApplication',
            'CollectCampaign', 'DoGoodEvent'
        )
    )

    class Meta(BaseActivitySerializer.Meta):
        model = Finish


from bluebottle.activity_pub.serializers.federated_activities import *  # noqa
