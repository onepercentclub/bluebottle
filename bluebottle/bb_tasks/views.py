from django.db.models.query_utils import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from bluebottle.bluebottle_drf2.permissions import IsAuthorOrReadOnly
from bluebottle.tasks.models import Task, TaskMember, TaskFile, Skill
from bluebottle.utils.serializers import DefaultSerializerMixin
from bluebottle.bb_projects.permissions import IsProjectOwnerOrReadOnly
from bluebottle.tasks.serializers import (
    BaseTaskMemberSerializer, TaskFileSerializer, TaskPreviewSerializer,
    MyTaskMemberSerializer, SkillSerializer, MyTasksSerializer)

from .permissions import IsMemberOrAuthorOrReadOnly

from tenant_extras.drf_permissions import TenantConditionalOpenClose


class TaskPreviewList(generics.ListAPIView):
    model = Task
    serializer_class = TaskPreviewSerializer
    paginate_by = 8
    filter_fields = ('status', 'skill',)

    def get_queryset(self):
        qs = super(TaskPreviewList, self).get_queryset()

        project_slug = self.request.QUERY_PARAMS.get('project', None)
        if project_slug:
            qs = qs.filter(project__slug=project_slug)

        country = self.request.QUERY_PARAMS.get('country', None)
        if country:
            qs = qs.filter(project__country=country)

        text = self.request.QUERY_PARAMS.get('text', None)
        if text:
            qs = qs.filter(Q(title__icontains=text) |
                           Q(description__icontains=text))

        ordering = self.request.QUERY_PARAMS.get('ordering', None)

        if ordering == 'newest':
            qs = qs.order_by('-created')
        elif ordering == 'deadline':
            qs = qs.order_by('deadline')

        qs = qs.exclude(status=Task.TaskStatuses.closed)

        return qs.filter(project__status__viewable=True)


class TaskList(DefaultSerializerMixin, generics.ListCreateAPIView):
    model = Task
    paginate_by = 8
    paginate_by_param = 'page_size'

    permission_classes = (TenantConditionalOpenClose, IsProjectOwnerOrReadOnly,)
    filter_fields = ('status', 'author')

    def get_queryset(self):
        qs = super(TaskList, self).get_queryset()

        project_slug = self.request.QUERY_PARAMS.get('project', None)
        if project_slug:
            qs = qs.filter(project__slug=project_slug)

        text = self.request.QUERY_PARAMS.get('text', None)
        if text:
            qs = qs.filter(Q(title__icontains=text) |
                           Q(description__icontains=text))

        ordering = self.request.QUERY_PARAMS.get('ordering', None)

        if ordering == 'newest':
            qs = qs.order_by('-created')
        elif ordering == 'deadline':
            qs = qs.order_by('deadline')

        return qs

    def pre_save(self, obj):
        obj.author = self.request.user


class MyTaskList(generics.ListCreateAPIView):
    model = Task
    paginate_by = 8
    filter_fields = ('author',)
    permission_classes = (IsProjectOwnerOrReadOnly,)
    serializer_class = MyTasksSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return Task.objects.filter(author=self.request.user)
        return Task.objects.none()

    def pre_save(self, obj):
        obj.author = self.request.user


class TaskDetail(DefaultSerializerMixin, generics.RetrieveUpdateAPIView):
    model = Task
    permission_classes = (TenantConditionalOpenClose, IsAuthorOrReadOnly,)


class MyTaskDetail(DefaultSerializerMixin,
                   generics.RetrieveUpdateDestroyAPIView):
    model = Task
    permission_classes = (TenantConditionalOpenClose, IsAuthorOrReadOnly,)


class TaskMemberList(generics.ListCreateAPIView):
    model = TaskMember
    serializer_class = BaseTaskMemberSerializer
    paginate_by = 50
    filter_fields = ('task', 'status',)
    permission_classes = (TenantConditionalOpenClose,
                          IsAuthenticatedOrReadOnly,)
    queryset = model.objects.all()

    def pre_save(self, obj):
        # When creating a task member it should always be by the
        # request.user and have status 'applied'
        obj.member = self.request.user
        obj.status = TaskMember.TaskMemberStatuses.applied


class MyTaskMemberList(generics.ListAPIView):
    model = TaskMember
    serializer_class = MyTaskMemberSerializer

    def get_queryset(self):
        queryset = super(MyTaskMemberList, self).get_queryset()
        # valid_statuses = [TaskMember.TaskMemberStatuses.accepted,
        # TaskMember.TaskMemberStatuses.realized]
        return queryset.filter(
            member=self.request.user)  # , status__in=valid_statuses)


class TaskMemberDetail(generics.RetrieveUpdateDestroyAPIView):
    model = TaskMember
    serializer_class = BaseTaskMemberSerializer

    permission_classes = (TenantConditionalOpenClose,
                          IsMemberOrAuthorOrReadOnly,)


class TaskFileList(generics.ListCreateAPIView):
    model = TaskFile
    serializer_class = TaskFileSerializer
    paginate_by = 50
    filter_fields = ('task',)
    permission_classes = (TenantConditionalOpenClose,
                          IsAuthenticatedOrReadOnly,)

    def pre_save(self, obj):
        # When creating a task file the author should always be
        # by the request.user
        obj.author = self.request.user


class TaskFileDetail(generics.RetrieveUpdateAPIView):
    model = TaskFile
    serializer_class = TaskFileSerializer

    permission_classes = (TenantConditionalOpenClose, IsAuthorOrReadOnly,)


class SkillList(generics.ListAPIView):
    model = Skill
    serializer_class = SkillSerializer


class UsedSkillList(SkillList):
    def get_queryset(self):
        qs = super(UsedSkillList, self).get_queryset()
        skill_ids = Task.objects.values_list('skill',
                                                      flat=True).distinct()
        return qs.filter(id__in=skill_ids)
