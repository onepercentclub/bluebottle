from django.db.models.query_utils import Q

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from . import get_project_model
from .models import (
    ProjectTheme, ProjectPhase, ProjectBudgetLine, ProjectDetailField)
from .serializers import (
    ManageProjectSerializer, ProjectPreviewSerializer, ProjectThemeSerializer,
    ProjectSerializer, ProjectPhaseSerializer, ProjectBudgetLineSerializer,
    ProjectDetailFieldSerializer)
from .permissions import IsProjectOwner, IsProjectOwnerOrReadOnly

PROJECT_MODEL = get_project_model()


class ProjectPreviewList(generics.ListAPIView):
    model = PROJECT_MODEL
    serializer_class = ProjectPreviewSerializer
    paginate_by = 8
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    def get_queryset(self):
        qs = PROJECT_MODEL.objects.filter(status__viewable=True)

        # For some reason the query fails if the country filter is defined before this.
        ordering = self.request.QUERY_PARAMS.get('ordering', None)

        if ordering == 'newest':
            qs = qs.order_by('-created')
        elif ordering == 'title':
            qs = qs.order_by('title')
        elif ordering == 'deadline':
            qs = qs.order_by('projectcampaign__deadline')

        country = self.request.QUERY_PARAMS.get('country', None)
        if country:
            qs = qs.filter(projectplan__country=country)

        theme = self.request.QUERY_PARAMS.get('theme', None)
        if theme:
            qs = qs.filter(projectplan__theme_id=theme)

        status = self.request.QUERY_PARAMS.get('status', None)
        if status:
            qs = qs.filter(Q(status_id=status))

        text = self.request.QUERY_PARAMS.get('text', None)
        if text:
            qs = qs.filter(Q(title__icontains=text) |
                           Q(pitch__icontains=text) |
                           Q(description__icontains=text))

        return qs.all()


class ProjectPreviewDetail(generics.RetrieveAPIView):
    model = PROJECT_MODEL
    serializer_class = ProjectPreviewSerializer

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


class ProjectList(generics.ListAPIView):
    model = PROJECT_MODEL
    serializer_class = ProjectSerializer
    paginate_by = 10

    def get_queryset(self):
        qs = super(ProjectList, self).get_queryset()
        status = self.request.QUERY_PARAMS.get('status', None)
        if status:
            qs = qs.filter(Q(status_id=status))
        return qs.filter(status__viewable=True)


class ProjectDetail(generics.RetrieveAPIView):
    model = PROJECT_MODEL
    serializer_class = ProjectSerializer

    def get_queryset(self):
        qs = super(ProjectDetail, self).get_queryset()
        return qs


class ProjectDetailFieldList(generics.ListAPIView):
    model = ProjectDetailField
    serializer_class = ProjectDetailFieldSerializer


class ManageProjectList(generics.ListCreateAPIView):
    model = PROJECT_MODEL
    serializer_class = ManageProjectSerializer
    permission_classes = (IsAuthenticated, )
    paginate_by = 10

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
        obj.owner = self.request.user


class ManageProjectDetail(generics.RetrieveUpdateAPIView):
    model = PROJECT_MODEL
    serializer_class = ManageProjectSerializer
    permission_classes = (IsProjectOwner, )


class ProjectThemeList(generics.ListAPIView):
    model = ProjectTheme
    serializer_class = ProjectThemeSerializer
    paginate_by = 10


class ProjectThemeDetail(generics.RetrieveAPIView):
    model = ProjectTheme
    serializer_class = ProjectThemeSerializer


class ManageProjectBudgetLineList(generics.ListCreateAPIView):
    model = ProjectBudgetLine
    serializer_class = ProjectBudgetLineSerializer
    permission_classes = (IsProjectOwnerOrReadOnly, )
    paginate_by = 20


class ManageProjectBudgetLineDetail(generics.RetrieveUpdateDestroyAPIView):
    model = ProjectBudgetLine
    serializer_class = ProjectBudgetLineSerializer
    permission_classes = (IsProjectOwnerOrReadOnly, )
