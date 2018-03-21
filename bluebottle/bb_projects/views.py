from dateutil import parser
import datetime
from django.db.models.query_utils import Q

from django.db.models import F
from django.db.models.aggregates import Count
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from bluebottle.projects.models import Project, ProjectPhaseLog, ProjectDocument
from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.projects.serializers import (
    ProjectThemeSerializer, ProjectPhaseSerializer,
    ProjectPhaseLogSerializer, ProjectDocumentSerializer,
    ProjectTinyPreviewSerializer, ProjectSerializer, ProjectPreviewSerializer, ManageProjectSerializer)
from bluebottle.utils.utils import get_client_ip
from bluebottle.utils.views import (
    ListAPIView, RetrieveAPIView, ListCreateAPIView, RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView, OwnerListViewMixin
)
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission, RelatedResourceOwnerPermission,
)
from bluebottle.projects.permissions import IsEditableOrReadOnly, CanEditOwnRunningProjects
from .models import ProjectTheme, ProjectPhase


class ProjectPagination(BluebottlePagination):
    page_size = 8


class TinyProjectPagination(BluebottlePagination):
    page_size = 10000


class ProjectListSearchMixin(object):

    def search(self, qs, query):
        # Apply filters
        status = query.getlist(u'status[]', None)
        if status:
            qs = qs.filter(status__slug__in=status)
        else:
            status = query.get('status', None)
            if status:
                qs = qs.filter(status__slug=status)

        country = query.get('country', None)
        if country:
            qs = qs.filter(country=country)

        location = query.get('location', None)
        if location:
            qs = qs.filter(location=location)

        category = query.get('category', None)
        if category:
            qs = qs.filter(categories__slug=category)

        theme = query.get('theme', None)
        if theme:
            qs = qs.filter(theme_id=theme)

        money_needed = query.get('money_needed', None)
        if money_needed:
            qs = qs.filter(amount_needed__gt=0)

        skill = query.get('skill', None)
        if skill:
            qs.select_related('task')
            qs = qs.filter(task__skill=skill).distinct()

        anywhere = query.get('anywhere', None)
        if anywhere:
            qs = qs.filter(Q(task__id__isnull=False), Q(task__location__isnull=True) | Q(task__location='')).distinct()

        start = query.get('start', None)
        if start:
            qs.select_related('task')

            tz = timezone.get_current_timezone()
            start_date = tz.localize(
                datetime.datetime.combine(parser.parse(start), datetime.datetime.min.time())
            )

            end = query.get('end', start)
            end_date = tz.localize(
                datetime.datetime.combine(parser.parse(end), datetime.datetime.max.time())
            )

            qs = qs.filter(
                Q(task__type='event', task__deadline__range=[start_date, end_date]) |
                Q(task__type='ongoing', task__deadline__gte=start_date)
            ).distinct()

        project_type = query.get('project_type', None)
        if project_type == 'volunteering':
            qs = qs.annotate(Count('task')).filter(task__count__gt=0)
        elif project_type == 'funding':
            qs = qs.filter(amount_asked__gt=0)
        elif project_type == 'voting':
            qs = qs.filter(status__slug__in=['voting', 'voting-done'])

        text = query.get('text', None)
        if text:
            qs = qs.filter(Q(title__icontains=text) |
                           Q(location__name__icontains=text) |
                           Q(pitch__icontains=text) |
                           Q(description__icontains=text))

        return self._ordering(query.get('ordering', None), qs, status)

    def _ordering(self, ordering, queryset, status):
        if ordering == 'deadline':
            queryset = queryset.order_by('status', 'deadline', 'id')
        elif ordering == 'amount_needed':
            # Add the percentage that is still needed to the query and sort on that.
            # This way we do not have to take currencies into account
            queryset = queryset.annotate(percentage_needed=F('amount_needed') / (F('amount_asked') + 1))
            queryset = queryset.order_by('status', 'percentage_needed', 'id')
            queryset = queryset.filter(amount_needed__gt=0)
        elif ordering == 'newest':
            queryset = queryset.extra(
                select={'has_campaign_started': 'campaign_started is null'})
            queryset = queryset.order_by('status', 'has_campaign_started',
                                         '-campaign_started', '-created', 'id')
        elif ordering == 'popularity':
            queryset = queryset.order_by('status', '-popularity', 'id')
            if status == 5:
                queryset = queryset.filter(amount_needed__gt=0)

        elif ordering:
            queryset = queryset.order_by('status', ordering)

        return queryset


class ProjectTinyPreviewList(ProjectListSearchMixin, OwnerListViewMixin, ListAPIView):
    queryset = Project.objects.all()
    pagination_class = TinyProjectPagination
    serializer_class = ProjectTinyPreviewSerializer

    owner_filter_field = 'owner'

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def get_queryset(self):
        qs = super(ProjectTinyPreviewList, self).get_queryset()
        query = self.request.query_params
        qs = self.search(qs, query=query)
        qs = qs.order_by('created')
        return qs.filter(status__viewable=True)


class ProjectPreviewList(ProjectListSearchMixin, OwnerListViewMixin, ListAPIView):
    queryset = Project.objects.all()
    pagination_class = ProjectPagination
    serializer_class = ProjectPreviewSerializer

    owner_filter_field = 'owner'

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def get_queryset(self):
        qs = super(ProjectPreviewList, self).get_queryset()
        query = self.request.query_params
        qs = self.search(qs, query)
        qs.select_related('task')
        return qs.filter(status__viewable=True)


class ProjectPreviewDetail(RetrieveAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectPreviewSerializer
    lookup_field = 'slug'

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def get_queryset(self):
        qs = super(ProjectPreviewDetail, self).get_queryset()
        return qs


class ProjectPhasePagination(BluebottlePagination):
    page_size = 20


class ProjectPhaseList(ListAPIView):
    queryset = ProjectPhase.objects.all()
    serializer_class = ProjectPhaseSerializer
    pagination_class = ProjectPhasePagination
    filter_fields = ('viewable',)

    def get_query(self):
        qs = ProjectPhase.objects

        name = self.request.query_params.get('name', None)
        text = self.request.query_params.get('text')

        qs = qs.order_by('sequence')

        if name:
            qs = qs.filter(Q(name__icontains=name))

        if text:
            qs = qs.filter(Q(description__icontains=text))

        return qs.all()


class ProjectPhaseDetail(RetrieveAPIView):
    queryset = ProjectPhase.objects.all()
    serializer_class = ProjectPhaseSerializer


class ProjectPhaseLogList(ListAPIView):
    queryset = ProjectPhaseLog.objects.all()
    serializer_class = ProjectPhaseLogSerializer
    pagination_class = BluebottlePagination

    def get_queryset(self):
        qs = super(ProjectPhaseLogList, self).get_queryset()
        return qs


class ProjectPhaseLogDetail(RetrieveAPIView):
    queryset = ProjectPhase.objects.all()
    serializer_class = ProjectPhaseLogSerializer


class ProjectList(OwnerListViewMixin, ListAPIView):
    queryset = Project.objects.all()
    pagination_class = BluebottlePagination
    serializer_class = ProjectSerializer

    owner_filter_field = 'owner'
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def get_queryset(self):
        qs = super(ProjectList, self).get_queryset()
        status = self.request.query_params.get('status', None)
        if status:
            qs = qs.filter(Q(status_id=status))
        return qs.filter(status__viewable=True)


class ProjectDetail(RetrieveAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'slug'

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )


class ManageProjectPagination(BluebottlePagination):
    page_size = 100


class ManageProjectList(ListCreateAPIView):
    queryset = Project.objects.all()
    pagination_class = ManageProjectPagination
    serializer_class = ManageProjectSerializer
    permission_classes = (ResourceOwnerPermission, )

    def get_queryset(self):
        """
        Overwrite the default to only return the Projects the currently logged
        in user owns.
        """
        queryset = super(ManageProjectList, self).get_queryset()
        if not isinstance(self.request.user, AnonymousUser):
            user = self.request.user
            queryset = queryset.filter(Q(owner=user) |
                                       Q(task_manager=user) |
                                       Q(promoter=user))
        queryset = queryset.order_by('-created')
        return queryset

    def perform_create(self, serializer):
        self.check_permissions(self.request)

        serializer.save(
            owner=self.request.user, status=ProjectPhase.objects.order_by('sequence').all()[0]
        )


class ManageProjectDetail(RetrieveUpdateAPIView):
    queryset = Project.objects.all()
    permission_classes = (
        ResourceOwnerPermission,
        OneOf(IsEditableOrReadOnly, CanEditOwnRunningProjects)
    )
    serializer_class = ManageProjectSerializer
    lookup_field = 'slug'

    def get_object(self):
        # Call the superclass
        object = super(ManageProjectDetail, self).get_object()

        # store the current state
        self.current_status = object.status

        return object


class ProjectThemeList(ListAPIView):
    serializer_class = ProjectThemeSerializer
    queryset = ProjectTheme.objects.all().filter(disabled=False)


class ProjectUsedThemeList(ProjectThemeList):
    def get_queryset(self):
        qs = super(ProjectUsedThemeList, self).get_queryset()
        theme_ids = Project.objects.filter(
            status__viewable=True).values_list('theme', flat=True).distinct()
        return qs.filter(id__in=theme_ids)


class ProjectThemeDetail(RetrieveAPIView):
    queryset = ProjectTheme.objects.all()
    serializer_class = ProjectThemeSerializer


class ManageProjectDocumentPagination(BluebottlePagination):
    page_size = 20


class ManageProjectDocumentList(OwnerListViewMixin, ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectDocumentSerializer
    pagination_class = ManageProjectDocumentPagination
    filter = ('project', )
    permission_classes = (RelatedResourceOwnerPermission, )

    owner_filter_field = 'project__owner'

    def perform_create(self, serializer):
        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        serializer.save(
            author=self.request.user, ip_address=get_client_ip(self.request)
        )


class ManageProjectDocumentDetail(RetrieveUpdateDestroyAPIView):
    queryset = ProjectDocument.objects.all()
    serializer_class = ProjectDocumentSerializer
    pagination_class = ManageProjectDocumentPagination
    filter = ('project', )

    permission_classes = (
        OneOf(ResourcePermission, RelatedResourceOwnerPermission),
    )

    def perform_update(self, serializer):
        serializer.save(
            author=self.request.user, ip_address=get_client_ip(self.request)
        )
