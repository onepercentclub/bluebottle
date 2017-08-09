from dateutil import parser
from datetime import datetime

from django.db.models.query_utils import Q
from django.utils import timezone

import django_filters
from rest_framework import generics, filters, serializers
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.projects.permissions import RelatedProjectOwnerPermission
from bluebottle.tasks.models import Task, TaskMember, TaskFile, Skill
from bluebottle.tasks.serializers import (BaseTaskSerializer,
                                          BaseTaskMemberSerializer, TaskFileSerializer,
                                          TaskPreviewSerializer, MyTaskMemberSerializer,
                                          SkillSerializer, MyTasksSerializer)
from bluebottle.utils.permissions import (OwnerOrReadOnlyPermission, AuthenticatedOrReadOnlyPermission,
                                          TenantConditionalOpenClose, OwnerOrParentOwnerOrAdminPermission)
from bluebottle.utils.views import (PrivateFileView, ListAPIView, ListCreateAPIView,
                                    RetrieveUpdateDestroyAPIView, RetrieveUpdateAPIView)
from .permissions import (ActiveProjectOrReadOnlyPermission, MemberOrOwnerOrReadOnlyPermission)


def day_start(date_str):
    date_combined = datetime.combine(parser.parse(date_str), datetime.min.time())
    return timezone.get_current_timezone().localize(date_combined)


def day_end(date_str):
    date_combined = datetime.combine(parser.parse(date_str), datetime.max.time())
    return timezone.get_current_timezone().localize(date_combined)


def get_dates_query(query, start_date, end_date):
    # User searches for tasks on a specific day.
    if start_date or end_date:
        start = day_start(start_date)
        if start_date and not end_date or (start_date and start_date is end_date):
            end = day_end(start_date)
        else:
            end = day_end(end_date)

        query = query.filter(Q(type='event', deadline__range=[start, end]) |
                             Q(type='ongoing', deadline__gte=start))

    return query


def get_midnight_datetime(dt):
    return timezone.get_current_timezone().localize(dt.combine(dt, dt.max.time()))


class TaskPreviewPagination(BluebottlePagination):
    page_size_query_param = 'page_size'
    page_size = 8


class TaskPreviewFilter(filters.FilterSet):
    after = django_filters.DateTimeFilter(name='deadline', lookup_expr='gte')
    before = django_filters.DateTimeFilter(name='deadline', lookup_expr='lte')
    country = django_filters.NumberFilter(name='project__country')
    location = django_filters.NumberFilter(name='project__location')
    project = django_filters.CharFilter(name='project__slug')
    text = django_filters.MethodFilter(action='text_filter')

    def text_filter(self, queryset, filter):
        return queryset.filter(
            Q(title__icontains=filter) | Q(description__icontains=filter)
        )

    class Meta:
        model = Task
        fields = ['status', 'skill', ]


class FilterQSParams(object):

    def get_qs(self, qs):
        project_slug = self.request.query_params.get('project', None)
        if project_slug:
            qs = qs.filter(project__slug=project_slug)

        text = self.request.query_params.get('text', None)
        if text:
            qs = qs.filter(Q(title__icontains=text) |
                           Q(description__icontains=text))

        status = self.request.query_params.get('status', None)
        if status:
            qs = qs.filter(status=status)
        return qs


class TaskPreviewList(ListAPIView, FilterQSParams):
    queryset = Task.objects.all()
    serializer_class = TaskPreviewSerializer
    pagination_class = TaskPreviewPagination
    filter_class = TaskPreviewFilter

    def get_queryset(self):
        qs = super(TaskPreviewList, self).get_queryset()

        qs = self.get_qs(qs)

        # Searching for tasks can mean 2 things:
        # 1) Search for tasks a specifc day
        # 2) Search for tasks that take place over a period of time
        start_date = self.request.query_params.get('start', None)
        end_date = self.request.query_params.get('end', None)

        qs = get_dates_query(qs, start_date, end_date)

        ordering = self.request.query_params.get('ordering', None)

        if ordering == 'newest':
            qs = qs.order_by('-created')
        elif ordering == 'deadline':
            qs = qs.order_by('deadline')

        return qs.filter(project__status__viewable=True)


class BaseTaskList(ListCreateAPIView):
    queryset = Task.objects.all()
    pagination_class = TaskPreviewPagination
    permission_classes = (TenantConditionalOpenClose, RelatedProjectOwnerPermission,)

    def perform_create(self, serializer):
        if serializer.validated_data['project'].status.slug in (
                'closed', 'done-complete', 'done-incomplete', 'voting-done'):
            raise serializers.ValidationError('It is not allowed to add tasks to closed projects')

        serializer.validated_data['deadline'] = get_midnight_datetime(serializer.validated_data['deadline'])
        serializer.save(author=self.request.user)


class TaskList(BaseTaskList, FilterQSParams):
    serializer_class = BaseTaskSerializer
    filter_fields = ('status', 'author')

    def get_queryset(self):
        qs = super(TaskList, self).get_queryset()

        qs = self.get_qs(qs)

        # Searching for tasks can mean 2 things:
        # 1) Search for tasks a specifc day
        # 2) Search for tasks that take place over a period of time
        start_date = self.request.query_params.get('start', None)
        end_date = self.request.query_params.get('end', None)

        qs = get_dates_query(qs, start_date, end_date)

        ordering = self.request.query_params.get('ordering', None)

        if ordering == 'newest':
            qs = qs.order_by('-created')
        elif ordering == 'deadline':
            qs = qs.order_by('deadline')

        return qs


class MyTaskList(BaseTaskList):
    filter_fields = ('author',)
    serializer_class = MyTasksSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return Task.objects.filter(author=self.request.user)
        return Task.objects.none()


class TaskDetail(RetrieveUpdateAPIView):
    queryset = Task.objects.all()
    permission_classes = (TenantConditionalOpenClose,
                          OwnerOrReadOnlyPermission,)
    serializer_class = BaseTaskSerializer


class MyTaskDetail(RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    permission_classes = (TenantConditionalOpenClose, OwnerOrReadOnlyPermission,)
    serializer_class = MyTasksSerializer

    def perform_update(self, serializer):
        serializer.validated_data['deadline'] = get_midnight_datetime(serializer.validated_data['deadline'])
        serializer.save()


class TaskPagination(BluebottlePagination):
    page_size = 50


class TaskMemberList(ListCreateAPIView):
    serializer_class = BaseTaskMemberSerializer
    pagination_class = TaskPagination
    filter_fields = ('task', 'status',)
    permission_classes = (TenantConditionalOpenClose,
                          ActiveProjectOrReadOnlyPermission,
                          AuthenticatedOrReadOnlyPermission)
    queryset = TaskMember.objects.all()

    def perform_create(self, serializer):
        serializer.save(member=self.request.user, status=TaskMember.TaskMemberStatuses.applied)


class MyTaskMemberList(ListAPIView):
    queryset = TaskMember.objects.all()
    serializer_class = MyTaskMemberSerializer

    def get_queryset(self):
        queryset = super(MyTaskMemberList, self).get_queryset()
        return queryset.filter(member=self.request.user)


class TaskMemberDetail(RetrieveUpdateAPIView):
    queryset = TaskMember.objects.all()
    serializer_class = BaseTaskMemberSerializer

    permission_classes = (TenantConditionalOpenClose,
                          MemberOrOwnerOrReadOnlyPermission,)


class TaskMemberResumeView(PrivateFileView):
    queryset = TaskMember.objects
    field = 'resume'
    permission_classes = (OwnerOrParentOwnerOrAdminPermission,)


class TaskFileList(generics.ListCreateAPIView):
    queryset = TaskFile.objects.all()
    serializer_class = TaskFileSerializer
    pagination_class = TaskPagination
    filter_fields = ('task',)
    permission_classes = (TenantConditionalOpenClose,
                          IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TaskFileDetail(RetrieveUpdateAPIView):
    queryset = TaskFile.objects.all()
    serializer_class = TaskFileSerializer

    permission_classes = (TenantConditionalOpenClose, OwnerOrReadOnlyPermission,)


class SkillList(generics.ListAPIView):
    queryset = Skill.objects.filter(disabled=False)
    serializer_class = SkillSerializer


class UsedSkillList(SkillList):
    def get_queryset(self):
        qs = super(UsedSkillList, self).get_queryset()
        skill_ids = Task.objects.values_list('skill',
                                             flat=True).distinct()
        return qs.filter(id__in=skill_ids)
