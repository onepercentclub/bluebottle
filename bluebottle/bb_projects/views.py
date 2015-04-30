from bluebottle.utils.serializers import DefaultSerializerMixin, ManageSerializerMixin, PreviewSerializerMixin
from django.db.models.query_utils import Q

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from bluebottle.utils.model_dispatcher import get_project_model, get_project_phaselog_model
from .models import ProjectTheme, ProjectPhase
from .serializers import (ProjectThemeSerializer, ProjectPhaseSerializer, ProjectPhaseLogSerializer)
from .permissions import IsProjectOwner


PROJECT_MODEL = get_project_model()
PROJECT_PHASELOG_MODEL = get_project_phaselog_model()


class ProjectPreviewList(PreviewSerializerMixin, generics.ListAPIView):
    model = PROJECT_MODEL
    paginate_by = 8
    paginate_by_param = 'page_size'

    def get_queryset(self):
        query = self.request.QUERY_PARAMS
        qs = PROJECT_MODEL.objects.search(query=query)
        return qs.filter(status__viewable=True).all()


class ProjectPreviewDetail(PreviewSerializerMixin, generics.RetrieveAPIView):
    model = PROJECT_MODEL

    def get_queryset(self):
        qs = super(ProjectPreviewDetail, self).get_queryset()
        return qs


class ProjectPhaseList(generics.ListAPIView):
    model = ProjectPhase
    serializer_class = ProjectPhaseSerializer
    paginate_by = 10
    filter_fields = ('viewable',)

    def get_query(self):
        qs = ProjectPhase.objects

        name = self.request.QUERY_PARAMS.get('name',None)
        text = self.request.QUERY_PARAMS.get('text')

        qs = qs.order_by('sequence')

        if name:
            qs = qs.filter(Q(name__icontains=name))

        if text:
            qs = qs.filter(Q(description__icontains=text))

        return qs.all()


class ProjectPhaseDetail(generics.RetrieveAPIView):
    model = ProjectPhase
    serializer_class = ProjectPhaseSerializer


class ProjectPhaseLogList(generics.ListAPIView):
    model = PROJECT_PHASELOG_MODEL
    serializer_class = ProjectPhaseLogSerializer
    paginate_by = 10

    def get_queryset(self):
        qs = super(ProjectPhaseLogList, self).get_queryset()
        return qs


class ProjectPhaseLogDetail(generics.RetrieveAPIView):
    model = PROJECT_PHASELOG_MODEL
    serializer_class = ProjectPhaseLogSerializer


class ProjectList(DefaultSerializerMixin, generics.ListAPIView):
    model = PROJECT_MODEL
    paginate_by = 10

    def get_queryset(self):
        qs = super(ProjectList, self).get_queryset()
        status = self.request.QUERY_PARAMS.get('status', None)
        if status:
            qs = qs.filter(Q(status_id=status))
        return qs.filter(status__viewable=True)


class ProjectDetail(DefaultSerializerMixin, generics.RetrieveAPIView):
    model = PROJECT_MODEL

    def get_queryset(self):
        qs = super(ProjectDetail, self).get_queryset()
        return qs


class ManageProjectList(ManageSerializerMixin, generics.ListCreateAPIView):
    model = PROJECT_MODEL
    permission_classes = (IsAuthenticated, )
    paginate_by = 100

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


class ManageProjectDetail(ManageSerializerMixin, generics.RetrieveUpdateAPIView):
    model = PROJECT_MODEL
    permission_classes = (IsProjectOwner, IsEditableOrReadOnly)

    def get_object(self):
        # Call the superclass
        object = super(ManageProjectDetail, self).get_object()

        # store the current state
        self.current_status = object.status

        return object
        

class ProjectThemeList(generics.ListAPIView):
    model = ProjectTheme
    serializer_class = ProjectThemeSerializer


class ProjectUsedThemeList(ProjectThemeList):
    def get_queryset(self):
        qs = super(ProjectUsedThemeList, self).get_queryset()
        theme_ids = PROJECT_MODEL.objects.filter(status__viewable=True).values_list('theme', flat=True).distinct()
        return qs.filter(id__in=theme_ids)


class ProjectThemeDetail(generics.RetrieveAPIView):
    model = ProjectTheme
    serializer_class = ProjectThemeSerializer
