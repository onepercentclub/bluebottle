from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum
from django.db.models.query_utils import Q
from rest_framework import generics
from rest_framework.generics import ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bluebottle.bluebottle_drf2.permissions import IsAuthorOrReadOnly
from bluebottle.bluebottle_drf2.views import RetrieveUpdateDeleteAPIView
from bluebottle.utils.utils import get_client_ip
from bluebottle.projects.permissions import IsProjectOwnerOrReadOnly
from bluebottle.wallposts.models import WallPost

from .models import Task, TaskMember, TaskFile, Skill
from .permissions import  IsTaskAuthorOrReadOnly
from .serializers import (
    TaskSerializer, TaskMemberSerializer, TaskWallPostSerializer, TaskFileSerializer, TaskPreviewSerializer,
    SkillSerializer, MyTaskMemberSerializer)


class TaskPreviewList(generics.ListAPIView):
    model = Task
    serializer_class = TaskPreviewSerializer
    paginate_by = 8
    filter_fields = ('status', 'skill', )

    def get_queryset(self):
        qs = super(TaskPreviewList, self).get_queryset()

        project_slug = self.request.QUERY_PARAMS.get('project', None)
        if project_slug:
            qs = qs.filter(project__slug=project_slug)

        text = self.request.QUERY_PARAMS.get('text', None)
        if text:
            qs = qs.filter(Q(title__icontains=text) |
                           Q(description__icontains=text) |
                           Q(end_goal__icontains=text))

        ordering = self.request.QUERY_PARAMS.get('ordering', None)

        if ordering == 'newest':
            qs = qs.order_by('-created')
        elif ordering == 'deadline':
            qs = qs.order_by('deadline')

        qs = qs.exclude(status=Task.TaskStatuses.closed)

        return qs


class TaskList(generics.ListCreateAPIView):
    model = Task
    serializer_class = TaskSerializer
    paginate_by = 8
    permission_classes = (IsProjectOwnerOrReadOnly,)
    filter_fields = ('status', 'expertise', )

    def get_queryset(self):
        qs = super(TaskList, self).get_queryset()

        project_slug = self.request.QUERY_PARAMS.get('project', None)
        if project_slug:
            qs = qs.filter(project__slug=project_slug)

        text = self.request.QUERY_PARAMS.get('text', None)
        if text:
            qs = qs.filter(Q(title__icontains=text) |
                           Q(description__icontains=text) |
                           Q(end_goal__icontains=text))

        ordering = self.request.QUERY_PARAMS.get('ordering', None)

        if ordering == 'newest':
            qs = qs.order_by('-created')
        elif ordering == 'deadline':
            qs = qs.order_by('deadline')

        qs = qs.exclude(status=Task.TaskStatuses.closed)

        return qs

    def pre_save(self, obj):
        obj.author = self.request.user


class TaskDetail(generics.RetrieveUpdateAPIView):
    model = Task
    permission_classes = (IsAuthorOrReadOnly, )
    serializer_class = TaskSerializer


class TaskMemberList(generics.ListCreateAPIView):
    model = TaskMember
    serializer_class = TaskMemberSerializer
    paginate_by = 50
    filter_fields = ('task', )
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def pre_save(self, obj):
        # When creating a task member it should always be by the request.user and have status 'applied'
        obj.member = self.request.user
        obj.status = TaskMember.TaskMemberStatuses.applied


class MyTaskMemberList(generics.ListAPIView):
    model = TaskMember
    serializer_class = MyTaskMemberSerializer

    def get_queryset(self):
        queryset = super(MyTaskMemberList, self).get_queryset()
        # valid_statuses = [TaskMember.TaskMemberStatuses.accepted, TaskMember.TaskMemberStatuses.realized]
        return queryset.filter(member=self.request.user)#, status__in=valid_statuses)


class TaskMemberDetail(generics.RetrieveUpdateAPIView):
    model = TaskMember
    serializer_class = TaskMemberSerializer

    permission_classes = (IsTaskAuthorOrReadOnly, )


class TaskFileList(generics.ListCreateAPIView):
    model = TaskFile
    serializer_class = TaskFileSerializer
    paginate_by = 50
    filter_fields = ('task', )
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def pre_save(self, obj):
        # When creating a task file the author should always be by the request.user
        obj.author = self.request.user


class TaskFileDetail(generics.RetrieveUpdateAPIView):
    model = TaskFile
    serializer_class = TaskFileSerializer

    permission_classes = (IsAuthorOrReadOnly, )


class SkillList(generics.ListAPIView):
    model = Skill
    serializer_class = SkillSerializer

