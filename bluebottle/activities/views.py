from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point
from django.contrib.postgres.aggregates import BoolOr
from django.db.models import ExpressionWrapper, BooleanField, Case, When, Value, Count
from django.db.models import Sum, Q, F
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import response, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.activities.filters import ActivitySearchFilter
from bluebottle.activities.models import Activity, Contributor, Team, Invite
from bluebottle.activities.permissions import ActivityOwnerPermission
from bluebottle.activities.serializers import (
    ActivityLocation,
    ActivityLocationSerializer,
    ActivitySerializer,
    ActivityTransitionSerializer,
    RelatedActivityImageSerializer,
    RelatedActivityImageContentSerializer,
    ActivityPreviewSerializer,
    ContributorListSerializer,
    TeamTransitionSerializer,
    ActivityImageSerializer,
)
from bluebottle.activities.utils import TeamSerializer, InviteSerializer
from bluebottle.bluebottle_drf2.renderers import ElasticSearchJSONAPIRenderer
from bluebottle.collect.models import CollectContributor
from bluebottle.deeds.models import DeedParticipant
from bluebottle.files.models import RelatedImage
from bluebottle.files.views import ImageContentView
from bluebottle.funding.models import Donor
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.time_based.models import DateParticipant, PeriodParticipant
from bluebottle.time_based.serializers import TeamMemberSerializer
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission, TenantConditionalOpenClose
)
from bluebottle.utils.views import (
    ListAPIView, JsonApiViewMixin, RetrieveUpdateDestroyAPIView,
    CreateAPIView, RetrieveAPIView, ExportView, JsonApiElasticSearchPagination
)


@method_decorator(cache_page(60 * 60), name='dispatch')
class ActivityLocationList(JsonApiViewMixin, ListAPIView):
    serializer_class = ActivityLocationSerializer
    pagination_class = None
    model = Activity

    permission_classes = (
        TenantConditionalOpenClose,
    )

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Activity.objects.filter(status__in=("succeeded", "open", "full", "running"))

        collects = [
            activity for activity
            in queryset.annotate(
                position=F('collectactivity__location__position'),
                location_id=F('collectactivity__location__pk')
            ).exclude(position=Point(0, 0)).filter(position__isnull=False)
        ]

        periods = [
            activity for activity
            in queryset.annotate(
                position=F('timebasedactivity__periodactivity__location__position'),
                location_id=F('timebasedactivity__periodactivity__location__pk')
            ).exclude(position=Point(0, 0)).filter(position__isnull=False)
        ]

        dates = [
            activity for activity
            in queryset.annotate(
                position=F('timebasedactivity__dateactivity__slots__location__position'),
                location_id=F('timebasedactivity__dateactivity__slots__location__pk')
            ).exclude(position=Point(0, 0)).filter(position__isnull=False)
        ]

        fundings = [
            activity for activity
            in queryset.annotate(
                position=F('funding__initiative__place__position'),
                location_id=F('funding__initiative__place__pk')
            ).exclude(position=Point(0, 0)).filter(position__isnull=False)
        ]

        locations = list(set(
            ActivityLocation(
                pk=f'{model.JSONAPIMeta.resource_name}-{model.pk}-{model.location_id}',
                created=model.created,
                position=model.position,
                activity=model,
            ) for model in collects + dates + periods + fundings
        ))
        return sorted(locations, key=lambda location: location.created, reverse=True)


class ActivityPreviewList(JsonApiViewMixin, ListAPIView):
    serializer_class = ActivityPreviewSerializer
    model = Activity
    pagination_class = JsonApiElasticSearchPagination
    renderer_classes = (ElasticSearchJSONAPIRenderer, )

    def list(self, request, *args, **kwargs):
        result = self.filter_queryset(None)

        page = self.paginate_queryset(result)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(result, many=True)
        return response.Response(serializer.data)

    filter_backends = (
        ActivitySearchFilter,
    )

    permission_classes = (
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )


class ActivityDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateDestroyAPIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    model = Activity
    lookup_field = 'pk'

    permission_classes = (
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'location': ['location'],
        'owner': ['owner'],
        'contributors': ['contributors']
    }


class ContributorList(JsonApiViewMixin, ListAPIView):
    model = Contributor

    def get_queryset(self):
        return Contributor.objects.prefetch_related(
            'user', 'activity', 'contributions'
        ).instance_of(
            Donor,
            DateParticipant,
            PeriodParticipant,
            DeedParticipant,
            CollectContributor,
        ).filter(
            user=self.request.user
        ).exclude(
            status__in=['rejected', 'failed']
        ).exclude(
            donor__status__in=['new']
        ).order_by(
            '-created'
        ).annotate(
            total_duration=Sum(
                'contributions__timecontribution__value',
                filter=Q(contributions__status__in=['succeeded', 'new'])
            )
        )

    serializer_class = ContributorListSerializer

    pagination_class = None

    permission_classes = (IsAuthenticated,)


class ActivityImage(ImageContentView):
    queryset = Activity.objects
    field = 'image'
    allowed_sizes = ActivityImageSerializer.sizes


class RelatedActivityImageList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    def get_queryset(self):
        return RelatedImage.objects.filter(
            content_type=ContentType.objects.get_for_model(Activity)
        )

    serializer_class = RelatedActivityImageSerializer

    related_permission_classes = {
        'content_object': [
            OneOf(ResourcePermission, ActivityOwnerPermission),
        ]
    }

    permission_classes = []


class RelatedActivityImageContent(ImageContentView):
    def get_queryset(self):
        return RelatedImage.objects.filter(
            content_type__in=[
                ContentType.objects.get_by_natural_key('time_based', 'dateactivity'),
                ContentType.objects.get_by_natural_key('time_based', 'periodactivity'),
                ContentType.objects.get_by_natural_key('funding', 'funding'),
                ContentType.objects.get_by_natural_key('assignments', 'assignment'),
                ContentType.objects.get_by_natural_key('events', 'event'),
                ContentType.objects.get_by_natural_key('deeds', 'deed'),
                ContentType.objects.get_by_natural_key('collect', 'collectactivity'),
            ]
        )

    field = 'image'
    allowed_sizes = RelatedActivityImageContentSerializer.sizes


class ActivityTransitionList(TransitionList):
    serializer_class = ActivityTransitionSerializer
    queryset = Activity.objects.all()


class TeamList(JsonApiViewMixin, ListAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    permission_classes = [OneOf(ResourcePermission, ActivityOwnerPermission), ]

    def get_queryset(self, *args, **kwargs):
        queryset = super(TeamList, self).get_queryset(*args, **kwargs)

        activity_id = self.request.query_params.get('filter[activity_id]')
        if activity_id:
            queryset = queryset.filter(
                activity_id=activity_id
            )

        has_slot = self.request.query_params.get('filter[has_slot]')
        start = self.request.query_params.get('filter[start]')
        status = self.request.query_params.get('filter[status]')
        if status:
            queryset = queryset.filter(status=status)
        elif has_slot == 'false':
            queryset = queryset.filter(slot__start__isnull=True).exclude(
                status__in=['new', 'withdrawn', 'cancelled']
            )
        elif start == 'future':
            queryset = queryset.filter(
                slot__start__gt=timezone.now()
            )
        elif start == 'passed':
            queryset = queryset.filter(
                slot__start__lt=timezone.now()
            ).exclude(
                slot__start__isnull=True
            )

        if self.request.user.is_authenticated:
            queryset = queryset.filter(
                Q(activity__initiative__activity_managers=self.request.user) |
                Q(activity__owner=self.request.user) |
                Q(owner=self.request.user) |
                Q(status='open')
            ).annotate(
                has_members=Count('members')
            ).annotate(
                current_user=Case(
                    When(
                        has_members=0,
                        then=Value(False)
                    ),
                    default=BoolOr(
                        ExpressionWrapper(
                            Q(members__user=self.request.user),
                            output_field=BooleanField()
                        )
                    )
                )
            ).distinct().order_by('-current_user')
            if has_slot == 'false':
                queryset = queryset.order_by('-current_user', 'id')
            elif start == 'future':
                queryset = queryset.order_by('-current_user', 'slot__start')
            elif start == 'passed':
                queryset = queryset.order_by('-current_user', '-slot__start')

        else:
            queryset = self.queryset.filter(
                status='open'
            ).order_by('-id')

        return queryset


class TeamTransitionList(TransitionList):
    serializer_class = TeamTransitionSerializer
    queryset = Team.objects.all()


class TeamMembersList(JsonApiViewMixin, ListAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )
    queryset = PeriodParticipant.objects

    def get_queryset(self):
        if self.request.user.is_authenticated:
            queryset = self.queryset.filter(
                Q(user=self.request.user) |
                Q(team__owner=self.request.user) |
                Q(team__activity__owner=self.request.user) |
                Q(team__activity__initiative__activity_managers=self.request.user) |
                Q(status='accepted')
            ).order_by('-id')
        else:
            queryset = self.queryset.filter(
                status='accepted'
            ).order_by('-id')

        return queryset.filter(
            team_id=self.kwargs['team_id']
        ).distinct('user_id', 'id').order_by('-id', 'user_id')

    serializer_class = TeamMemberSerializer


class InviteDetailView(JsonApiViewMixin, RetrieveAPIView):
    permission_classes = [TenantConditionalOpenClose]
    queryset = Invite.objects.all()

    serializer_class = InviteSerializer


class TeamMembersExportView(ExportView):
    fields = (
        ('user__email', 'Email'),
        ('user__full_name', 'Name'),
        ('created', 'Registration Date'),
        ('status', 'Status'),
        ('is_team_captain', 'Team Captain'),
    )

    filename = 'team participants'
    model = Team

    def get_instances(self):
        return self.get_object().members.all()


class RelatedContributorListView(JsonApiViewMixin, ListAPIView):
    search_fields = ['user__first_name', 'user__last_name']
    filter_backends = [filters.SearchFilter]

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['display_member_names'] = MemberPlatformSettings.objects.get().display_member_names

        activity = Activity.objects.get(pk=self.kwargs['activity_id'])
        context['owners'] = [activity.owner] + list(activity.initiative.activity_managers.all())

        if self.request.user and self.request.user.is_authenticated and (
                self.request.user in context['owners'] or
                self.request.user.is_staff or
                self.request.user.is_superuser
        ):
            context['display_member_names'] = 'full_name'

        return context

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                queryset = self.queryset
            else:
                queryset = self.queryset.filter(
                    Q(user=self.request.user) |
                    Q(activity__owner=self.request.user) |
                    Q(activity__initiative__activity_manager=self.request.user) |
                    Q(status__in=('accepted', 'succeeded',))
                ).order_by('-id')
        else:
            queryset = self.queryset.filter(
                status__in=('accepted', 'succeeded',)
            ).order_by('-id')

        status = self.request.query_params.get('filter[status]')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.filter(
            activity_id=self.kwargs['activity_id']
        )
