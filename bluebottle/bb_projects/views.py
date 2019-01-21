import time
import datetime

from django.db.models.query_utils import Q
from django.utils import timezone

from django.contrib.auth.models import AnonymousUser

from dateutil import parser

from elasticsearch_dsl import Q as ESQ, SF
from rest_framework.response import Response

from bluebottle.projects import documents
from bluebottle.projects.models import Project, ProjectPhaseLog
from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.projects.serializers import (
    ProjectThemeSerializer, ProjectPhaseSerializer,
    ProjectPhaseLogSerializer, ProjectTinyPreviewSerializer,
    ProjectSerializer, ProjectPreviewSerializer, ManageProjectSerializer
)
from bluebottle.utils.views import (
    ListAPIView, RetrieveAPIView, ListCreateAPIView, RetrieveUpdateAPIView,
    OwnerListViewMixin, TranslatedApiViewMixin
)
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
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
    django_paginator_class = ESPaginator


class ProjectListSearchMixin(object):
    search_fields = (
        'country', 'location', 'theme', 'category',
        'skill', 'project_type', 'anywhere', 'start',
    )

    def _text_query(self, value):
        return (
            ESQ('match_phrase_prefix', title={'query': value, 'boost': 10}) |
            ESQ('match_phrase_prefix', pitch=value) |
            ESQ('match_phrase_prefix', story=value) |
            ESQ(
                'nested', path='location', query=(
                    ESQ('match_phrase_prefix', **{'location.name': value}) |
                    ESQ('match_phrase_prefix', **{'location.city': value})
                )
            ) |
            ESQ(
                'nested', path='task_set', query=(
                    ESQ('match_phrase_prefix', **{'task_set.title': value}) |
                    ESQ('match_phrase_prefix', **{'task_set.description': value}) |
                    ESQ('match_phrase_prefix', **{'task_set.location': value})
                )
            )
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
        return query & ESQ(
            'nested', path='location', query=ESQ('term', **{'location.id': value})
        )

    def _filter_theme(self, query, value):
        return query & ESQ('term', **{'theme.id': value})

    def _filter_category(self, query, value):
        return query & ESQ(
            'nested', path='categories', query=ESQ('term', **{'categories.id': value})
        )

    def _filter_skill(self, query, value):
        return query & ESQ('term', **{'skills': value})

    def _filter_project_type(self, query, value):
        if value == 'volunteering':
            return query & ESQ(
                'nested', path='task_set', query=ESQ('exists', field='task_set.title')
            )
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
            'nested',
            path='task_set',
            query=(
                ~ESQ('exists', field='task_set.location') |
                ESQ('term', **{'task_set.location_keyword': ''})
            )
        )

    def _filter_start(self, query, start):
        start = timezone.get_current_timezone().localize(parser.parse(start))
        if 'end' in self.request.query_params:
            end = timezone.get_current_timezone().localize(
                parser.parse(self.request.query_params['end'])
            )
        else:
            end = datetime.date.max

        return query & (
            ESQ(
                'nested', path='task_set', query=(
                    ESQ('term', **{'task_set.type': 'event'}) &
                    ESQ('range', **{
                        'task_set.deadline': {
                            'gte': start,
                            'lte': end
                        }
                    })
                )
            ) |
            ESQ(
                'nested', path='task_set', query=(
                    ESQ('term', **{'task_set.type': 'ongoing'}) &
                    ESQ('range', **{'task_set.deadline': {'gte': start}})
                )
            )
        )

    def _filter_owner(self, filter):
        user = self.request.user if self.request.user.is_authenticated else None
        return filter & ESQ('term', owner_id=user.pk)

    def _scoring(self):
        scoring = ESQ(
            'function_score',
            query=ESQ('exists', field='donations'),
            functions=[
                SF({
                    'script_score': {
                        'script': {
                            'source': 'doc["donations"].length * 3600000 / (now - doc["donations"].avg())',
                            'lang': 'expression',
                            'params': {
                                'now': time.time() * 1000,
                            }
                        },
                    },
                }),
            ]
        ) | ESQ(
            'function_score',
            query=ESQ('exists', field='task_members'),
            functions=[
                SF({
                    'script_score': {
                        'script': {
                            'source': 'doc["task_members"].length * 10000 / (now - doc["task_members"].avg())',
                            'lang': 'expression',
                            'params': {
                                'now': time.time() * 1000,
                            }
                        },
                    },
                }),
            ]
        ) | ESQ(
            'function_score',
            score_mode='sum',
            functions=[
                SF({
                    'filter': ESQ('terms', **{'status.slug': ['campaign', 'voting']}),
                    'weight': 30
                }),
                SF({
                    'filter': ESQ('term', **{'status.slug': 'done-complete'}),
                    'weight': 20
                }),
                SF({
                    'filter': ESQ('terms', **{'status.slug': ['done-incomplete', 'voting-done', 'refunded']}),
                    'weight': 10
                }),
            ]
        ) | ESQ(
            'function_score',
            functions=[
                SF({
                    'script_score': {
                        'script': {
                            'source': '(!doc["amount_needed"] && doc["people_needed"]) > 0 ? 4 : 0',
                            'lang': 'expression',
                        },
                    },
                }),
            ]
        )
        if self.request.user.is_authenticated:
            if self.request.user.location:
                scoring = scoring | ESQ(
                    'function_score',
                    boost=2,
                    functions=[
                        SF({
                            'gauss': {
                                'position': {
                                    'origin': self.request.user.location.position_tuple,
                                    'scale': "100km"
                                },
                            },
                        }),
                    ]
                ) | ESQ(
                    'function_score',
                    score_mode='first',
                    boost=2,
                    functions=[
                        SF({
                            'filter': {'exists': {'field': 'task_positions'}},
                            'gauss': {
                                'task_positions': {
                                    'origin': self.request.user.location.position_tuple,
                                    'scale': "100km"
                                },
                                'multi_value_mode': 'min',
                            },
                        }),
                        SF({
                            "script_score": {
                                "script": "0"
                            }
                        })
                    ]
                )

            if len(self.request.user.skills.all()):
                scoring = scoring | ESQ(
                    'function_score',
                    score_mode='first',
                    functions=[
                        SF({
                            'filter': ESQ('term', **{'skills': skill.id}),
                            'weight': 2
                        }) for skill in self.request.user.skills.all()
                    ]
                )

            if len(self.request.user.favourite_themes.all()):
                scoring = scoring | ESQ(
                    'function_score',
                    score_mode='first',
                    functions=[
                        SF({
                            'filter': ESQ('term', **{'themes': theme.id}),
                            'weight': 2
                        }) for theme in self.request.user.favourite_themes.all()
                    ]
                )

        return scoring

    def search(self, viewable=True):
        search = documents.ProjectDocument.search()
        if viewable:
            filter = ESQ('term', **{'status.viewable': True})
        else:
            filter = ESQ()

        for field in self.search_fields:
            value = self.request.query_params.get(field)
            if value:
                filter = getattr(self, '_filter_{}'.format(field))(filter, value)

        statuses = self.request.query_params.getlist('status[]')
        if statuses:
            filter = self._filter_status(filter, statuses)

        if not self.request.user.has_perm('projects.api_read_project'):
            filter = self._filter_owner(filter)

        ordering = self.request.query_params.get('ordering')
        if ordering and ordering != 'popularity':
            if ordering == 'deadline':
                sort = ('status.sequence', 'deadline')
            elif ordering == 'amount_needed':
                sort = ('status.sequence', 'amount_needed')
            elif ordering == 'newest':
                sort = ('status.sequence', '-campaign_started')
            elif ordering == 'status':
                sort = ('status.sequence', )

            query = search.query().filter(filter).sort(*sort)
        else:
            scoring = self._scoring()
            query = search.filter(filter).query(scoring)

        text = self.request.query_params.get('text')
        if text:
            return query.query(self._text_query(text))

        return query


class ProjectTinyPreviewList(ProjectListSearchMixin, ListAPIView):
    queryset = Project.objects.all()
    pagination_class = TinyProjectPagination
    serializer_class = ProjectTinyPreviewSerializer

    owner_filter_field = 'owner'

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def list(self, request):
        result = self.search().sort('created')
        page = self.paginate_queryset(result)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(result.to_queryset(), many=True)
        return Response(serializer.data)


class ProjectPreviewList(ProjectListSearchMixin, ListAPIView):
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


class ProjectThemeList(TranslatedApiViewMixin, ListAPIView):
    serializer_class = ProjectThemeSerializer
    queryset = ProjectTheme.objects.filter(disabled=False)


class ProjectUsedThemeList(ProjectThemeList):
    def get_queryset(self):
        qs = super(ProjectThemeList, self).get_queryset()
        theme_ids = Project.objects.filter(
            status__viewable=True).values_list('theme', flat=True).distinct()
        return qs.filter(id__in=theme_ids)


class ProjectThemeDetail(RetrieveAPIView):
    queryset = ProjectTheme.objects.all()
    serializer_class = ProjectThemeSerializer
