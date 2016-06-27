import django_filters

from django.db.models.query_utils import Q
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.bluebottle_drf2.permissions import IsAuthorOrReadOnly
from bluebottle.tasks.models import Task, TaskMember, TaskFile, Skill
from bluebottle.bb_projects.permissions import IsProjectOwnerOrReadOnly
from bluebottle.tasks.serializers import (BaseTaskSerializer,
    BaseTaskMemberSerializer, TaskFileSerializer, TaskPreviewSerializer,
    MyTaskMemberSerializer, SkillSerializer, MyTasksSerializer)

from .permissions import IsMemberOrAuthorOrReadOnly

from tenant_extras.drf_permissions import TenantConditionalOpenClose


class TaskPreviewPagination(BluebottlePagination):
    page_size = 8


class TaskPreviewFilter(filters.FilterSet):
    after = django_filters.DateTimeFilter(name='deadline', lookup_type='gte')
    before = django_filters.DateTimeFilter(name='deadline', lookup_type='lte')
    country = django_filters.NumberFilter(name='project__country')
    project = django_filters.CharFilter(name='project__slug')
    text = django_filters.MethodFilter(action='text_filter')

    def text_filter(self, queryset, filter):
        return queryset.filter(
            Q(title__icontains=filter) | Q(description__icontains=filter)
        )

    class Meta:
        model = Task
        fields = ['status', 'skill', ]


class TaskPreviewList(generics.ListAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskPreviewSerializer
    pagination_class = TaskPreviewPagination
    filter_class = TaskPreviewFilter

    def get_queryset(self):
        qs = super(TaskPreviewList, self).get_queryset()
        ordering = self.request.query_params.get('ordering', None)

        if ordering == 'newest':
            qs = qs.order_by('-created')
        elif ordering == 'deadline':
            qs = qs.order_by('deadline')

        qs = qs.exclude(status=Task.TaskStatuses.closed)

        return qs.filter(project__status__viewable=True)


class TaskList(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    pagination_class = TaskPreviewPagination
    serializer_class = BaseTaskSerializer
    permission_classes = (TenantConditionalOpenClose, IsProjectOwnerOrReadOnly,)
    filter_fields = ('status', 'author')

    def get_queryset(self):
        qs = super(TaskList, self).get_queryset()

        project_slug = self.request.query_params.get('project', None)
        if project_slug:
            qs = qs.filter(project__slug=project_slug)

        text = self.request.query_params.get('text', None)
        if text:
            qs = qs.filter(Q(title__icontains=text) |
                           Q(description__icontains=text))

        ordering = self.request.query_params.get('ordering', None)

        if ordering == 'newest':
            qs = qs.order_by('-created')
        elif ordering == 'deadline':
            qs = qs.order_by('deadline')

        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class MyTaskList(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    pagination_class = TaskPreviewPagination
    filter_fields = ('author',)
    permission_classes = (IsProjectOwnerOrReadOnly,)
    serializer_class = MyTasksSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return Task.objects.filter(author=self.request.user)
        return Task.objects.none()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TaskDetail(generics.RetrieveUpdateAPIView):
    queryset = Task.objects.all()
    permission_classes = (TenantConditionalOpenClose, IsAuthorOrReadOnly,)
    serializer_class = BaseTaskSerializer


class MyTaskDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    permission_classes = (TenantConditionalOpenClose, IsAuthorOrReadOnly,)
    serializer_class = MyTasksSerializer


class TaskPagination(BluebottlePagination):
    page_size = 50


class TaskMemberList(generics.ListCreateAPIView):
    serializer_class = BaseTaskMemberSerializer
    pagination_class = TaskPagination
    filter_fields = ('task', 'status',)
    permission_classes = (TenantConditionalOpenClose,
                          IsAuthenticatedOrReadOnly,)
    queryset = TaskMember.objects.all()

    def perform_create(self, serializer):
        serializer.save(member=self.request.user, status=TaskMember.TaskMemberStatuses.applied)


class MyTaskMemberList(generics.ListAPIView):
    queryset = TaskMember.objects.all()
    serializer_class = MyTaskMemberSerializer

    def get_queryset(self):
        queryset = super(MyTaskMemberList, self).get_queryset()
        # valid_statuses = [TaskMember.TaskMemberStatuses.accepted,
        # TaskMember.TaskMemberStatuses.realized]
        return queryset.filter(
            member=self.request.user)  # , status__in=valid_statuses)


class TaskMemberDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = TaskMember.objects.all()
    serializer_class = BaseTaskMemberSerializer

    permission_classes = (TenantConditionalOpenClose,
                          IsMemberOrAuthorOrReadOnly,)


class TaskFileList(generics.ListCreateAPIView):
    queryset = TaskFile.objects.all()
    serializer_class = TaskFileSerializer
    pagination_class = TaskPagination
    filter_fields = ('task',)
    permission_classes = (TenantConditionalOpenClose,
                          IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TaskFileDetail(generics.RetrieveUpdateAPIView):
    queryset = TaskFile.objects.all()
    serializer_class = TaskFileSerializer

    permission_classes = (TenantConditionalOpenClose, IsAuthorOrReadOnly,)


class SkillList(generics.ListAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer


class UsedSkillList(SkillList):
    def get_queryset(self):
        qs = super(UsedSkillList, self).get_queryset()
        skill_ids = Task.objects.values_list('skill',
                                                      flat=True).distinct()
        return qs.filter(id__in=skill_ids)
