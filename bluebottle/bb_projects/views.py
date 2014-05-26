from bluebottle.utils.serializers import DefaultSerializerMixin, ManageSerializerMixin, PreviewSerializerMixin
from django.db.models.query_utils import Q

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from bluebottle.utils.utils import get_project_model
from .models import ProjectTheme, ProjectPhase
from .serializers import (ProjectThemeSerializer, ProjectPhaseSerializer)
from .permissions import IsProjectOwner


PROJECT_MODEL = get_project_model()


class ProjectPreviewList(PreviewSerializerMixin, generics.ListAPIView):
    model = PROJECT_MODEL
    paginate_by = 8
    paginate_by_param = 'page_size'
    max_paginate_by = 100

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
        """
        Set the project owner and the status of the project.
        """
        obj.status = ProjectPhase.objects.order_by('sequence').all()[0]
        obj.owner = self.request.user


class ManageProjectDetail(ManageSerializerMixin, generics.RetrieveUpdateAPIView):
    model = PROJECT_MODEL
    permission_classes = (IsProjectOwner, )

    def get_object(self):
        # Call the superclass
        object = super(ManageProjectDetail, self).get_object()

        # store the current state
        self.current_status = object.status

        return object

    """
    Don't let the owner set a status with a sequence number higher than 2 
    They can set 1: plan-new or 2: plan-submitted

    TODO: This needs work. Maybe we could use a FSM for the project status
          transitions, e.g.: 
              https://pypi.python.org/pypi/django-fsm/1.2.0
    """
    def pre_save(self, obj):
        submit_status = ProjectPhase.objects.get(slug='plan-submitted')
        status_id = self.request.DATA.get('status')

        """
        TODO: what to do if the expected status (plan-submitted) is
              no found?! Hard fail?
        """
        if submit_status and status_id:
            max_sequence = submit_status.sequence
            new_status = ProjectPhase.objects.get(id=status_id)

            """
            Reset the status if the owner is trying to set the status
            higher than the max permitted, or the user is trying to
            set the status back to a lower state
            """
            if new_status and (new_status.sequence > max_sequence or new_status.sequence < self.current_status.sequence):
                obj.status = self.current_status


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
