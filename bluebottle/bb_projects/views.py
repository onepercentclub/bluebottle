from django.db.models.query_utils import Q

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from bluebottle.projects.models import Project, ProjectPhaseLog, ProjectDocument
from tenant_extras.drf_permissions import TenantConditionalOpenClose

from bluebottle.projects.serializers import (
    ProjectThemeSerializer, ProjectPhaseSerializer,
    ProjectPhaseLogSerializer, ProjectDocumentSerializer,
    ProjectTinyPreviewSerializer, ProjectSerializer, ProjectPreviewSerializer, ManageProjectSerializer)
from bluebottle.utils.utils import get_client_ip

from .models import ProjectTheme, ProjectPhase
from .permissions import IsProjectOwner, IsEditableOrReadOnly


class ProjectTinyPreviewList(generics.ListAPIView):
    queryset = Project.objects.all()
    paginate_by = 8
    paginate_by_param = 'page_size'
    serializer_class = ProjectTinyPreviewSerializer

    def get_queryset(self):
        query = self.request.query_params
        qs = Project.objects.search(query=query)
        return qs.filter(status__viewable=True)


class ProjectPreviewList(generics.ListAPIView):
    queryset = Project.objects.all()
    paginate_by = 8
    paginate_by_param = 'page_size'
    serializer_class = ProjectPreviewSerializer

    def get_queryset(self):
        query = self.request.query_params
        qs = Project.objects.search(query=query)
        return qs.filter(status__viewable=True)


class ProjectPreviewDetail(generics.RetrieveAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectPreviewSerializer
    def get_queryset(self):
        qs = super(ProjectPreviewDetail, self).get_queryset()
        return qs


class ProjectPhaseList(generics.ListAPIView):
    queryset = ProjectPhase.objects.all()
    serializer_class = ProjectPhaseSerializer
    paginate_by = 10
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


class ProjectPhaseDetail(generics.RetrieveAPIView):
    queryset = ProjectPhase.objects.all()
    serializer_class = ProjectPhaseSerializer


class ProjectPhaseLogList(generics.ListAPIView):
    queryset = ProjectPhaseLog.objects.all()
    serializer_class = ProjectPhaseLogSerializer
    paginate_by = 10

    def get_queryset(self):
        qs = super(ProjectPhaseLogList, self).get_queryset()
        return qs


class ProjectPhaseLogDetail(generics.RetrieveAPIView):
    queryset = ProjectPhase.objects.all()
    serializer_class = ProjectPhaseLogSerializer


class ProjectList(generics.ListAPIView):
    queryset = Project.objects.all()
    paginate_by = 10
    serializer_class = ProjectSerializer

    def get_queryset(self):
        qs = super(ProjectList, self).get_queryset()
        status = self.request.query_params.get('status', None)
        if status:
            qs = qs.filter(Q(status_id=status))
        return qs.filter(status__viewable=True)


class ProjectDetail(generics.RetrieveAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_queryset(self):
        qs = super(ProjectDetail, self).get_queryset()
        return qs


class ManageProjectList(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    permission_classes = (TenantConditionalOpenClose, IsAuthenticated, )
    paginate_by = 100
    serializer_class = ManageProjectSerializer

    def get_queryset(self):
        """
        Overwrite the default to only return the Projects the currently logged
        in user owns.
        """
        queryset = super(ManageProjectList, self).get_queryset()
        queryset = queryset.filter(owner=self.request.user)
        queryset = queryset.order_by('-created')
        return queryset

    def pre_save(self, obj):
        """
        Set the project owner and the status of the project.
        """
        obj.status = ProjectPhase.objects.order_by('sequence').all()[0]
        obj.owner = self.request.user


class ManageProjectDetail(generics.RetrieveUpdateAPIView):
    queryset = Project.objects.all()
    permission_classes = (IsProjectOwner, IsEditableOrReadOnly)
    serializer_class = ManageProjectSerializer

    def get_object(self):
        # Call the superclass
        object = super(ManageProjectDetail, self).get_object()

        # store the current state
        self.current_status = object.status

        return object


class ProjectThemeList(generics.ListAPIView):
    queryset = ProjectTheme.objects.all()
    serializer_class = ProjectThemeSerializer
    queryset = ProjectTheme.objects.all().filter(disabled=False)


class ProjectUsedThemeList(ProjectThemeList):
    def get_queryset(self):
        qs = super(ProjectUsedThemeList, self).get_queryset()
        theme_ids = Project.objects.filter(
            status__viewable=True).values_list('theme', flat=True).distinct()
        return qs.filter(id__in=theme_ids)


class ProjectThemeDetail(generics.RetrieveAPIView):
    queryset = ProjectTheme.objects.all()
    serializer_class = ProjectThemeSerializer


class ManageProjectDocumentList(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectDocumentSerializer
    paginate_by = 20
    filter = ('project', )

    def pre_save(self, obj):
        obj.author = self.request.user
        obj.ip_address = get_client_ip(self.request)


class ManageProjectDocumentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProjectDocument.objects.all()
    serializer_class = ProjectDocumentSerializer
    paginate_by = 20
    filter = ('project', )

    def pre_save(self, obj):
        obj.author = self.request.user
        obj.ip_address = get_client_ip(self.request)
