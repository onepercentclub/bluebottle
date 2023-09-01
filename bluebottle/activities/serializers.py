import hashlib
from builtins import object
from collections import namedtuple
from datetime import datetime

import dateutil
from django.conf import settings
from django.urls import reverse
from django.utils.timezone import get_current_timezone, now
from geopy.distance import distance, lonlat
from rest_framework import serializers
from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField, ResourceRelatedField
)
from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer, Serializer

from bluebottle.activities.models import Contributor, Activity, Team
from bluebottle.collect.serializers import CollectActivityListSerializer, CollectActivitySerializer, \
    CollectContributorListSerializer
from bluebottle.deeds.serializers import (
    DeedListSerializer, DeedSerializer, DeedParticipantListSerializer
)
from bluebottle.files.models import RelatedImage
from bluebottle.files.serializers import ImageSerializer, ImageField
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.funding.serializers import (
    FundingListSerializer, FundingSerializer,
    DonorListSerializer, TinyFundingSerializer
)
from bluebottle.geo.serializers import PointSerializer
from bluebottle.time_based.serializers import (
    DateActivityListSerializer,
    PeriodActivityListSerializer,

    DateActivitySerializer,
    PeriodActivitySerializer, DateParticipantSerializer, PeriodParticipantSerializer,
    DateParticipantListSerializer, PeriodParticipantListSerializer,
)
from bluebottle.utils.fields import PolymorphicSerializerMethodResourceRelatedField
from bluebottle.utils.serializers import (
    MoneySerializer
)
from bluebottle.utils.utils import get_current_language

ActivityLocation = namedtuple('Position', ['pk', 'created', 'position', 'activity'])


class ActivityLocationRelationSerializer(Serializer):
    class JSONAPIMeta:
        resource_name = 'activity-location-relations'


class ActivityLocationSerializer(Serializer):
    position = PointSerializer()
    activity = PolymorphicSerializerMethodResourceRelatedField(
        ActivityLocationRelationSerializer,
        read_only=True,
        model=ActivityLocation,
    )

    def get_activity(self, obj):
        return obj.activity

    class JSONAPIMeta:
        resource_name = 'activity-locations'


IMAGE_SIZES = {
    'preview': '292x164',
    'small': '320x180',
    'large': '600x337',
    'cover': '1568x882'
}


class ActivityImageSerializer(ImageSerializer):
    sizes = IMAGE_SIZES
    content_view_name = 'activity-image'
    relationship = 'activity_set'


class ActivityPreviewSerializer(ModelSerializer):
    theme = serializers.SerializerMethodField()
    expertise = serializers.SerializerMethodField()
    initiative = serializers.CharField(source='initiative.title')

    image = serializers.SerializerMethodField()
    matching_properties = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    slot_count = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    has_multiple_locations = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()

    type = serializers.SerializerMethodField()

    target = MoneySerializer(read_only=True)
    amount_raised = MoneySerializer(read_only=True)
    amount_matching = MoneySerializer(read_only=True)
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()
    highlight = serializers.BooleanField()
    contribution_duration = serializers.SerializerMethodField()

    collect_type = serializers.SerializerMethodField()

    def get_start(self, obj):
        if hasattr(obj, 'slots') and obj.slots:
            upcoming = self.context['request'].GET.get('filter[upcoming]') == '1'
            slots = self.get_filtered_slots(obj, only_upcoming=upcoming)
            if slots:
                return slots[0].start

        elif obj.start and len(obj.start) == 1:
            return obj.start[0]

    def get_end(self, obj):
        if hasattr(obj, 'slots') and obj.slots:
            upcoming = self.context['request'].GET.get('filter[upcoming]') == '1'

            tz = get_current_timezone()
            try:
                start, end = (
                    dateutil.parser.parse(date).astimezone(tz)
                    for date in self.context['request'].GET.get('filter[date]').split(',')
                )
            except (ValueError, AttributeError):
                start = None
                end = None

            if upcoming or (start and start >= now()):
                ends = [
                    slot.end for slot in obj.slots
                    if (
                        slot.status not in ['draft', 'cancelled'] and
                        (not start or dateutil.parser.parse(slot.start).date() >= start.date()) and
                        (not end or dateutil.parser.parse(slot.end).date() <= end.date())
                    )
                ]
            else:
                ends = [
                    slot.end for slot in obj.slots
                    if (
                        slot.status not in ['draft', 'cancelled'] and
                        (not start or dateutil.parser.parse(slot.end).date() > start.date()) and
                        (not end or dateutil.parser.parse(slot.end).date() <= end.date())
                    )
                ]
            if ends:
                return max(ends)
        elif obj.end and len(obj.end) == 1:
            return obj.end[0]

    def get_expertise(self, obj):
        try:
            return [
                expertise.name
                for expertise in obj.expertise or []
                if expertise.language == get_current_language()
            ][0]
        except IndexError:
            pass

    def get_contribution_duration(self, obj):
        if hasattr(obj, 'contribution_duration'):
            if len(obj.contribution_duration) == 0:
                return {}
            elif len(obj.contribution_duration) == 1:
                return {
                    'period': obj.contribution_duration[0].period,
                    'value': obj.contribution_duration[0].value,
                }

    def get_collect_type(self, obj):
        try:
            return [
                collect_type.name
                for collect_type in getattr(obj, 'collect_type', [])
                if collect_type.language == get_current_language()
            ][0]
        except IndexError:
            pass

    def get_theme(self, obj):
        try:
            return [
                theme.name
                for theme in obj.theme or []
                if theme.language == get_current_language()
            ][0]
        except IndexError:
            pass

    def get_type(self, obj):
        return obj.type.replace('activity', '')

    def get_location(self, obj):
        location = False
        if hasattr(obj, 'slots') and obj.slots:
            slots = self.get_filtered_slots(obj)

            if len(set(slot.formatted_address for slot in self.get_filtered_slots(obj))) == 1:
                location = slots[0]
        elif type == 'funding':
            places = [location for location in obj.location if location.type == 'place']
            if places:
                location = places[0]
        elif len(obj.location):
            order = ['location', 'office', 'place', 'initiative_office', 'impact_location']
            location = sorted(obj.location, key=lambda l: order.index(l.type))[0]

        if location:
            if location.locality:
                return f'{location.locality}, {location.country_code}'
            else:
                return location.country

    def get_image(self, obj):
        if obj.image:
            hash = hashlib.md5(obj.image.file.encode('utf-8')).hexdigest()
            if obj.image.type == 'activity':
                url = reverse('activity-image', args=(obj.image.id, IMAGE_SIZES['large'], ))
            if obj.image.type == 'initiative':
                url = reverse('initiative-image', args=(obj.image.id, IMAGE_SIZES['large'], ))

            return f'{url}?_={hash}'

    def get_matching_properties(self, obj):
        user = self.context['request'].user
        matching = {'skill': False, 'theme': False, 'location': False}

        if not user.is_authenticated or not obj.is_upcoming:
            return matching

        if 'skills' not in self.context:
            self.context['skills'] = [skill.pk for skill in user.skills.all()]

        if 'themes' not in self.context:
            self.context['themes'] = [theme.pk for theme in user.favourite_themes.all()]

        if 'location' not in self.context:
            if user.location and user.location.position:
                self.context['location'] = user.location

            if user.place and user.place.position:
                self.context['location'] = user.place

        matching = {'location': False}
        matching['skill'] = obj.expertise[0].id in self.context['skills'] if obj.expertise else False
        matching['theme'] = obj.theme[0].id in self.context['themes'] if obj.theme else False

        if obj.is_online:
            matching['location'] = True
        elif 'location' in self.context and obj.position:
            positions = [obj.position] if 'lat' in obj.position else obj.position

            dist = min(
                distance(
                    lonlat(pos['lon'], pos['lat']),
                    lonlat(*self.context['location'].position.tuple)
                ) for pos in positions

            )

            if dist.km < settings.MATCHING_DISTANCE:
                matching['location'] = True

        return matching

    def get_filtered_slots(self, obj, only_upcoming=False):
        tz = get_current_timezone()

        try:
            start, end = (
                dateutil.parser.parse(date).astimezone(tz)
                for date in self.context['request'].GET.get('filter[date]').split(',')
            )
        except (ValueError, AttributeError):
            start = None
            end = None

        if hasattr(obj, 'slots') and obj.slots:
            return [
                slot for slot in obj.slots
                if (
                    slot.status not in ['draft', 'cancelled'] and
                    (not only_upcoming or datetime.fromisoformat(slot.start).date() >= now().date()) and
                    (not start or dateutil.parser.parse(slot.start).date() >= start.date()) and
                    (not end or dateutil.parser.parse(slot.end).date() <= end.date())
                )
            ]
        else:
            return []

    def get_slot_count(self, obj):
        if hasattr(obj, 'slots') and obj.slots:
            return len(self.get_filtered_slots(obj, only_upcoming=True))

    def get_is_online(self, obj):
        if hasattr(obj, 'slots') and obj.slots:
            return all(slot.is_online for slot in self.get_filtered_slots(obj))
        else:
            return obj.is_online

    def get_has_multiple_locations(self, obj):
        return len(set(slot.formatted_address for slot in self.get_filtered_slots(obj))) > 1

    def get_is_full(self, obj):
        slots = self.get_filtered_slots(obj)

        if len(slots):
            return all(slot.status != 'open' for slot in slots)
        elif obj.type == 'period':
            return obj.status != 'open'

    class Meta(object):
        model = Activity
        fields = (
            'id', 'slug', 'type', 'title', 'theme', 'expertise',
            'initiative', 'image', 'matching_properties', 'target',
            'amount_raised', 'target', 'amount_matching', 'end', 'start',
            'status', 'location', 'team_activity',
            'slot_count', 'is_online', 'has_multiple_locations', 'is_full',
            'collect_type', 'highlight', 'contribution_duration',
        )

    class JSONAPIMeta:
        resource_name = 'activities/preview'


class ActivityListSerializer(PolymorphicModelSerializer):

    polymorphic_serializers = [
        FundingListSerializer,
        DeedListSerializer,
        CollectActivityListSerializer,
        DateActivityListSerializer,
        PeriodActivityListSerializer,
    ]

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'image': 'bluebottle.activities.serializers.ActivityImageSerializer',
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'initiative.place': 'bluebottle.geo.serializers.GeolocationSerializer',
        'goals': 'bluebottle.impact.serializers.ImpactGoalSerializer',
        'collect_type': 'bluebottle.collect.serializers.CollectTypeSerializer',
    }

    class Meta(object):
        model = Activity
        meta_fields = (
            'permissions',
            'created',
            'updated',
            'matching_properties',
        )

    class JSONAPIMeta:
        included_resources = [
            'owner',
            'initiative',
            'location',
            'image',
            'goals',
            'goals.type',
            'initiative.image',
            'initiative.place',
            'initiative.location',
        ]


class ActivitySerializer(PolymorphicModelSerializer):

    polymorphic_serializers = [
        FundingSerializer,
        DeedSerializer,
        CollectActivitySerializer,
        DateActivitySerializer,
        PeriodActivitySerializer,
    ]

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'goals': 'bluebottle.impact.serializers.ImpactGoalSerializer',
        'goals.type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'image': 'bluebottle.activities.serializers.ActivityImageSerializer',
        'initiative.activity_managers': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative.promoter': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'initiative.place': 'bluebottle.geo.serializers.GeolocationSerializer',
        'initiative.organization': 'bluebottle.organizations.serializers.OrganizationSerializer',
        'initiative.organization_contact': 'bluebottle.organizations.serializers.OrganizationContactSerializer',
    }

    class Meta(object):
        model = Activity
        meta_fields = (
            'permissions',
            'transitions',
            'created',
            'updated',
            'errors',
            'required',
        )

    class JSONAPIMeta(object):
        included_resources = [
            'owner',
            'image',
            'initiative',
            'goals',
            'goals.type',
            'location',
            'initiative.image',
            'initiative.place',
            'initiative.location',
            'initiative.activity_managers',
            'initiative.promoter',
            'initiative.organization',
            'initiative.organization_contact',
        ]


class TinyActivityListSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        TinyFundingSerializer,
        DateActivityListSerializer,
        PeriodActivityListSerializer,
    ]

    class Meta(object):
        model = Activity
        fields = ('id', 'slug', 'title', )
        meta_fields = (
            'created', 'updated',
        )


class ContributorSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        DonorListSerializer,
        DateParticipantSerializer,
        PeriodParticipantSerializer
    ]

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.ActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = [
            'user',
            'activity',
        ]

    class Meta(object):
        model = Contributor
        meta_fields = (
            'created', 'updated',
        )


class ContributorListSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        DonorListSerializer,
        DateParticipantListSerializer,
        PeriodParticipantListSerializer,
        DeedParticipantListSerializer,
        CollectContributorListSerializer
    ]

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.TinyActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'slots': 'bluebottle.time_based.serializers.SlotParticipantSerializer',
        'slots.slot': 'bluebottle.time_based.serializers.DateActivitySlotSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = [
            'user',
            'activity',
            'slots',
            'slots.slot',
        ]

    class Meta(object):
        model = Contributor
        meta_fields = (
            'created', 'updated',
        )


class ActivityTransitionSerializer(TransitionSerializer):
    resource = PolymorphicResourceRelatedField(ActivitySerializer, queryset=Activity.objects.all())
    field = 'states'

    included_serializers = {
        'resource': 'bluebottle.activities.serializers.ActivitySerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource']
        resource_name = 'activities/transitions'


class RelatedActivityImageSerializer(ModelSerializer):
    image = ImageField(required=False, allow_null=True)
    resource = PolymorphicResourceRelatedField(
        ActivitySerializer,
        queryset=Activity.objects.all(),
        source='content_object'
    )

    included_serializers = {
        'resource': 'bluebottle.activities.serializers.ActivitySerializer',
        'image': 'bluebottle.activities.serializers.RelatedActivityImageContentSerializer',
    }

    class Meta(object):
        model = RelatedImage
        fields = ('image', 'resource', )

    class JSONAPIMeta(object):
        included_resources = [
            'resource', 'image',
        ]

        resource_name = 'related-activity-images'


class RelatedActivityImageContentSerializer(ImageSerializer):
    sizes = {
        'large': '600',
    }
    content_view_name = 'related-activity-image-content'
    relationship = 'relatedimage_set'


class TeamTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Team.objects.all())
    field = 'states'

    included_serializers = {
        'resource': 'bluebottle.activities.utils.TeamSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource']
        resource_name = 'activities/team-transitions'
