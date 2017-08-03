from django.db.models.query_utils import Q

from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import IsAuthenticated

from bluebottle.projects.models import Project, ProjectPhaseLog, ProjectDocument
from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.projects.serializers import (
    ProjectThemeSerializer, ProjectPhaseSerializer,
    ProjectPhaseLogSerializer, ProjectDocumentSerializer,
    ProjectTinyPreviewSerializer, ProjectSerializer, ProjectPreviewSerializer, ManageProjectSerializer)
from bluebottle.utils.utils import get_client_ip
from bluebottle.utils.views import (
    ListAPIView, RetrieveAPIView, ListCreateAPIView, RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView
)
from bluebottle.utils.permissions import OwnerPermission
from bluebottle.projects.permissions import IsEditableOrReadOnly
from .models import ProjectTheme, ProjectPhase


class ProjectPagination(BluebottlePagination):
    page_size = 8


class TinyProjectPagination(BluebottlePagination):
    page_size = 10000


class ProjectTinyPreviewList(ListAPIView):
    queryset = Project.objects.all()
    pagination_class = TinyProjectPagination
    serializer_class = ProjectTinyPreviewSerializer

    def get_queryset(self):
        query = self.request.query_params
        qs = Project.objects.search(query=query)
        qs = qs.order_by('created')
        return qs.filter(status__viewable=True)


class ProjectPreviewList(ListAPIView):
    queryset = Project.objects.all()
    pagination_class = ProjectPagination
    serializer_class = ProjectPreviewSerializer

    def get_queryset(self):
        query = self.request.query_params
        qs = Project.objects.search(query)
        qs.select_related('task')
        return qs.filter(status__viewable=True)


class ProjectPreviewDetail(RetrieveAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectPreviewSerializer
    lookup_field = 'slug'

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


class ProjectList(ListAPIView):
    queryset = Project.objects.all()
    pagination_class = BluebottlePagination
    serializer_class = ProjectSerializer

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


class ManageProjectPagination(BluebottlePagination):
    page_size = 100


class ManageProjectList(ListCreateAPIView):
    queryset = Project.objects.all()
    pagination_class = ManageProjectPagination
    serializer_class = ManageProjectSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        """
        Overwrite the default to only return the Projects the currently logged
        in user owns.
        """
        queryset = super(ManageProjectList, self).get_queryset()
        if not isinstance(self.request.user, AnonymousUser):
            queryset = queryset.filter(owner=self.request.user)
        queryset = queryset.order_by('-created')
        return queryset

    def perform_create(self, serializer):
        serializer.save(
            owner=self.request.user, status=ProjectPhase.objects.order_by('sequence').all()[0]
        )


class ManageProjectDetail(RetrieveUpdateAPIView):
    queryset = Project.objects.all()
    permission_classes = (OwnerPermission, IsEditableOrReadOnly,)
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


class ManageProjectDocumentList(ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectDocumentSerializer
    pagination_class = ManageProjectDocumentPagination
    filter = ('project', )

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user, ip_address=get_client_ip(self.request)
        )


class ManageProjectDocumentDetail(RetrieveUpdateDestroyAPIView):
    queryset = ProjectDocument.objects.all()
    serializer_class = ProjectDocumentSerializer
    pagination_class = ManageProjectDocumentPagination
    filter = ('project', )

    def perform_update(self, serializer):
        serializer.save(
            author=self.request.user, ip_address=get_client_ip(self.request)
        )
