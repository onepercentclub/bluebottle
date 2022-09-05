from builtins import object

from datetime import datetime, time
import dateutil
import hashlib
from django.urls import reverse

from django.utils.timezone import get_current_timezone, now
from django.conf import settings


from rest_framework import serializers
from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField, ResourceRelatedField
)
from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer

from geopy.distance import distance, lonlat

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
from bluebottle.time_based.serializers import (
    DateActivityListSerializer,
    PeriodActivityListSerializer,

    DateActivitySerializer,
    PeriodActivitySerializer, DateParticipantSerializer, PeriodParticipantSerializer,
    DateParticipantListSerializer, PeriodParticipantListSerializer,
)
from bluebottle.utils.serializers import (
    MoneySerializer
)
from bluebottle.utils.utils import get_current_language

IMAGE_SIZES = {
    'preview': '300x168',
    'small': '320x180',
    'large': '600x337',
    'cover': '960x540'
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
    matching_options = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    location_info = serializers.SerializerMethodField()
    date_info = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    target = MoneySerializer(read_only=True)
    amount_raised = MoneySerializer(read_only=True)
    start = serializers.CharField()
    deadline = serializers.CharField(source='end')

    def get_expertise(self, obj):
        try:
            return [
                expertise.name
                for expertise in obj.expertise or []
                if expertise.language == get_current_language()
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
        if obj.location:
            location = obj.location[0]
            if location.city:
                return f'{location.city}, {location.country_code}'
            else:
                return location.country

    def get_image(self, obj):
        if obj.image:
            hash = hashlib.md5(obj.image.file.encode('utf-8')).hexdigest()
            if obj.image.type == 'activity':
                url = reverse('activity-image', args=(obj.image.id, IMAGE_SIZES['large'], ))
            if obj.image.type == 'initiative':
                url = reverse('activity-image', args=(obj.image.id, IMAGE_SIZES['large'], ))

            return f'{url}?_={hash}'

    def get_matching_options(self, obj):
        user = self.context['request'].user
        matching = {'skill': False, 'theme': False, 'location': False}

        if not user.is_authenticated or obj.status != 'open':
            return matching

        if 'skills' not in self.context:
            self.context['skills'] = [skill.pk for skill in user.skills.all()]

        if 'themes' not in self.context:
            self.context['themes'] = [theme.pk for theme in user.favourite_themes.all()]

        if 'location' not in self.context:
            self.context['location'] = user.location or user.place

        matching = {}
        matching['skill'] = obj.expertise[0].id in self.context['skills'] if obj.expertise else False
        matching['theme'] = obj.theme[0].id in self.context['themes'] if obj.theme else False

        if obj.is_online:
            matching['location'] = True
        elif self.context['location']:
            positions = [obj.position] if 'lat' in obj.position else obj.position

            dist = min(
                distance(
                    lonlat(pos['lat'], pos['lon']),
                    lonlat(*self.context['location'].position.tuple)
                ) for pos in positions

            )

            if dist.km < settings.MATCHING_DISTANCE:
                matching['location'] = True

        return matching

    def get_filtered_slots(self, obj, only_upcoming=False):
        tz = get_current_timezone()

        try:
            start = dateutil.parser.parse(
                self.context['request'].GET.get('filter[start]')
            ).astimezone(tz)
        except (ValueError, TypeError):
            start = None

        try:
            end = datetime.combine(
                dateutil.parser.parse(
                    self.context['request'].GET.get('filter[end]'),
                ),
                time.max
            ).astimezone(tz)
        except (ValueError, TypeError):
            end = None

        return [
            slot for slot in obj.slots
            if (
                slot.status not in ['draft', 'cancelled'] and
                (not only_upcoming or slot.start >= now()) and
                (not start or slot.start >= start) and
                (not end or slot.end <= end)
            )
        ]

    def get_location_info(self, obj):
        info = {}

        if obj.slots:
            slots = self.get_filtered_slots(obj)

            info['is_online'] = all(slot.is_online for slot in slots)

            locations = set(
                (slot.locality, slot.country, slot.formatted_address)
                for slot in slots
            )

            if len(locations) > 1:
                info['has_multiple'] = True
            else:
                location = tuple(locations)[0]
                info['location'] = {
                    'locality': location[0],
                    'country': {'code': location[1]},
                    'formattedAddress': location[2],
                }

        return info

    def get_date_info(self, obj):
        return {}

    class Meta(object):
        model = Activity
        fields = (
            'id', 'slug', 'type', 'title', 'theme', 'expertise',
            'initiative', 'image', 'matching_options', 'target',
            'amount_raised', 'deadline', 'start', 'date_info', 'location_info',
            'status', 'location'
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
        'initiative.location': 'bluebottle.geo.serializers.LocationSerializer',
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
        'initiative.location': 'bluebottle.geo.serializers.LocationSerializer',
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
