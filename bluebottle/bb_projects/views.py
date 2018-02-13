from dateutil import parser
import datetime
from django.db.models.query_utils import Q

from django.db.models import F
from django.db.models.aggregates import Count
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone


from elasticsearch_dsl import Q as ESQ, SF
from rest_framework.response import Response
import six

from bluebottle.projects.models import Project, ProjectPhaseLog, ProjectDocument
from bluebottle.projects import documents
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


from django.core.paginator import Paginator


class ESPaginator(Paginator):
    def page(self, *args, **kwargs):
        page = super(ESPaginator, self).page(*args, **kwargs)
        page.object_list = page.object_list.to_queryset()
        return page


class ProjectPagination(BluebottlePagination):
    page_size = 8
    django_paginator_class = ESPaginator


class TinyProjectPagination(BluebottlePagination):
    page_size = 10000


class ProjectListSearchMixin(object):

    def search(self):
        search = documents.ProjectDocument.search()
        query = ESQ()

        text = self.request.query_params.get('text')
        if text:
            query = query & (
                ESQ('match', title={'query': text, 'boost': 2}) |
                ESQ('match', pitch=text) |
                ESQ('match', story=text) |
                ESQ('nested', path='task_set', query=ESQ('match', **{'task_set.title': text})) |
                ESQ('nested', path='task_set', query=ESQ('match', **{'task_set.description': text}))
            )

        statuses = self.request.query_params.getlist('status[]')
        if statuses:
            filters = ESQ(
                'bool',
                should=[
                    ESQ('term', **{'status.slug': status}) for status in statuses
                ]
            )

            query = query & filters

        country = self.request.query_params.get('country', None)
        if country:
            filter = ESQ('term', **{'country.id': country})
            query = query & filter

        location = self.request.query_params.get('location', None)
        if location:
            filter = ESQ('term', **{'location.id': country})
            query = query & filter

        theme = self.request.query_params.get('theme', None)
        if theme:
            filter = ESQ('term', **{'theme.id': theme})
            query = query & filter

        category = self.request.query_params.get('category', None)
        if category:
            filter = ESQ('nested', path='categories', query=ESQ('term', **{'categories.id': category}))
            query = query & filter

        skill = self.request.query_params.get('skill', None)
        if skill:
            filter = ESQ(
                'nested',
                path='task_set',
                query=ESQ('term', **{'task_set.skill.id': category})
            )
            query = query & filter

        project_type = self.request.query_params.get('project_type', None)
        if project_type == 'volunteering':
            filter = ESQ(
                'script',
                script="return doc.containsKey('task_set') "
            )
            query = query & filter
        elif project_type == 'funding':
            filter = ESQ('range', amount_asked={'gt': 0})
            query = query & filter
        elif project_type == 'voting':
            filters = ESQ(
                'bool',
                should=[
                    ESQ('term', **{'status.slug': status}) for status in ['voting', 'voting-done']
                ]
            )
            query = query & filter

        anywhere = self.request.query_params.get('anywhere', None)
        if anywhere:
            filter = ESQ('nested', path='task_set', query=~ESQ('exists', field='task_set.location'))
            query = query & filter


        return search.query(
            'function_score', query=query, field_value_factor={'field': 'popularity'}
        )

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

    def list(self, request):
        result = self.search()

        page = self.paginate_queryset(result)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(result.to_queryset(), many=True)
        return Response(serializer.data)


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


class ProjectPhaseList(ListAPIView):
    queryset = ProjectPhase.objects.all()
    serializer_class = ProjectPhaseSerializer
    pagination_class = BluebottlePagination
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
