from bluebottle.projects.models import ProjectBudgetLine, ProjectDetailField
from bluebottle.projects.serializers import (
    ProjectBudgetLineSerializer, ProjectDetailFieldSerializer)
from django.db.models.query_utils import Q

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Project, ProjectTheme
from .serializers import (
    ManageProjectSerializer, ProjectPreviewSerializer, ProjectThemeSerializer,
    ProjectSerializer)
from .permissions import IsProjectOwner, IsProjectOwnerOrReadOnly


class ProjectPreviewList(generics.ListAPIView):
    model = Project
    serializer_class = ProjectPreviewSerializer
    paginate_by = 8
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    def get_queryset(self):
        qs = Project.objects

        # For some reason the query fails if the country filter is defined before this.
        ordering = self.request.QUERY_PARAMS.get('ordering', None)

        if ordering == 'newest':
            qs = qs.order_by('-created')
        elif ordering == 'title':
            qs = qs.order_by('title')
        elif ordering == 'deadline':
            qs = qs.order_by('projectcampaign__deadline')
        elif ordering == 'money_needed':
            qs = qs.order_by('money_needed')

        country = self.request.QUERY_PARAMS.get('country', None)
        if country:
            qs = qs.filter(projectplan__country=country)

        theme = self.request.QUERY_PARAMS.get('theme', None)
        if theme:
            qs = qs.filter(projectplan__theme_id=theme)

        text = self.request.QUERY_PARAMS.get('text', None)
        if text:
            qs = qs.filter(Q(title__icontains=text) |
                           Q(pitch__icontains=text) |
                           Q(description__icontains=text))

        return qs.all()


class ProjectPreviewDetail(generics.RetrieveAPIView):
    model = Project
    serializer_class = ProjectPreviewSerializer

    def get_queryset(self):
        qs = super(ProjectPreviewDetail, self).get_queryset()
        return qs


class ProjectList(generics.ListAPIView):
    model = Project
    serializer_class = ProjectSerializer
    paginate_by = 10
    filter_fields = ('phase', )

    def get_queryset(self):
        qs = super(ProjectList, self).get_queryset()
        return qs


class ProjectDetail(generics.RetrieveAPIView):
    model = Project
    serializer_class = ProjectSerializer

    def get_queryset(self):
        qs = super(ProjectDetail, self).get_queryset()
        return qs


class ProjectDetailFieldList(generics.ListAPIView):
    model = ProjectDetailField
    serializer_class = ProjectDetailFieldSerializer


class ManageProjectList(generics.ListCreateAPIView):
    model = Project
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
    model = Project
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

