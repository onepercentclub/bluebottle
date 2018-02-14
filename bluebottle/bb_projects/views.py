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
    search_fields = (
        'text', 'country', 'location', 'theme', 'category',
        'skill', 'project_type', 'anywhere', 'start',
    )

    def _filter_text(self, query, value):
        return query & (
            ESQ('match', title={'query': value, 'boost': 2}) |
            ESQ('match', pitch=value) |
            ESQ('match', story=value) |
            ESQ('nested', path='task_set', query=ESQ('match', **{'task_set.title': value})) |
            ESQ('nested', path='task_set', query=ESQ('match', **{'task_set.description': value}))
        )

    def _filter_status(self, query, value):
        return query & ESQ(
            'bool',
            should=[
                ESQ('term', **{'status.slug': status}) for status in value
            ]
        )

    def _filter_country(self, query, value):
        return query & ESQ('term', **{'country.id': value})

    def _filter_location(self, query, value):
        return query & ESQ('term', **{'country.id': value})

    def _filter_theme(self, query, value):
        return query & ESQ('term', **{'theme.id': value})

    def _filter_category(self, query, value):
        return query & ESQ(
            'nested', path='categories', query=ESQ('term', **{'categories.id': value})
        )

    def _filter_skill(self, query, value):
        return value & ESQ(
            'nested',
            path='task_set',
            query=ESQ('term', **{'task_set.skill.id': value})
        )

    def _filter_project_type(self, query, value):
        if value == 'volunteering':
            return query & ESQ('nested', path='task_set', query=ESQ('exists', field='task_set.title'))
        elif value == 'funding':
            return query & ESQ('range', amount_asked={'gt': 0})
        elif value == 'voting':
            return query & ESQ(
                'bool',
                should=[
                    ESQ('term', **{'status.slug': status}) for status in ['voting', 'voting-done']
                ]
            )
        else:
            return query

    def _filter_anywhere(self, query, value):
        return query & ESQ(
            'nested', path='task_set', query=~ESQ('exists', field='task_set.location')
        )

    def _filter_start(self, query, start):
        end = self.request.query_params.get('end', start)

        return query & (
            ESQ('nested', path='task_set', query=(
                ESQ('term', **{'task_set.type': 'event'}) &
                ESQ('range', **{'task_set.deadline': {'gte': start, 'lte': end}})
            )) |
            ESQ('nested', path='task_set', query=(
                ESQ('term', **{'task_set.type': 'ongoing'}) &
                ESQ('range', **{'task_set.deadline': {'gte': start}})
            ))
        )

    def search(self):
        search = documents.ProjectDocument.search()
        query = ESQ()

        for field in self.search_fields:
            value = self.request.query_params.get(field)
            if value:
                query = getattr(self, '_filter_{}'.format(field))(query, value)

        statuses = self.request.query_params.getlist('status[]')
        if statuses:
            query = self._filter_status(query, statuses)

        return search.query(
            query & (
                ESQ('bool', boost=0.5, should=(
                    ESQ('term', **{'status.slug': 'campaign'}) | ESQ('term', **{'status.slug': 'campaign'})
                )) |
                ESQ('nested', path='donation_set', score_mode='sum', query=ESQ(
                    'function_score',
                    boost=0.1,
                    functions=[SF(
                        'gauss',
                        **{'donation_set.created': {
                            'origin': timezone.now(),
                            'offset': "1d",
                            'scale': "30d"
                        }}
                    )]
                )) |
                ESQ('nested', path='vote_set', score_mode='sum', query=ESQ(
                    'function_score',
                    functions=[SF(
                        'gauss',
                        **{'vote_set.created': {
                            'origin': timezone.now(),
                            'offset': "1d",
                            'scale': "30d"
                        }}
                    )]
                )) |
                ESQ('nested', path='vote_set', score_mode='sum', query=ESQ(
                    'function_score',
                    functions=[SF(
                        'gauss',
                        **{'vote_set.created': {
                            'origin': timezone.now(),
                            'offset': "1d",
                            'scale': "30d"
                        }}
                    )]
                ))
            )
        )

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
        result = self.search().extra(explain=True)

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
