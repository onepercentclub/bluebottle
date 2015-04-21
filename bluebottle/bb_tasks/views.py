from django.db.models.query_utils import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from bluebottle.bluebottle_drf2.permissions import IsAuthorOrReadOnly
from bluebottle.utils.serializers import DefaultSerializerMixin
from bluebottle.bb_projects.permissions import IsProjectOwnerOrReadOnly

from .permissions import IsMemberOrAuthorOrReadOnly
from .serializers import (
    BaseTaskMemberSerializer, TaskFileSerializer, TaskPreviewSerializer,
    MyTaskMemberSerializer, SkillSerializer, MyTasksSerializer)

from bluebottle.utils.model_dispatcher import get_task_model, get_taskmember_model, get_taskfile_model, \
    get_task_skill_model

BB_TASK_MODEL = get_task_model()
BB_TASKMEMBER_MODEL = get_taskmember_model()
BB_TASKFILE_MODEL = get_taskfile_model()
BB_SKILL_MODEL = get_task_skill_model()


class TaskPreviewList(generics.ListAPIView):
    model = BB_TASK_MODEL
    serializer_class = TaskPreviewSerializer
    paginate_by = 8
    filter_fields = ('status', 'skill', )

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

        qs = qs.exclude(status=BB_TASK_MODEL.TaskStatuses.closed)

        return qs.filter(project__status__viewable=True)


class TaskList(DefaultSerializerMixin, generics.ListCreateAPIView):
    model = BB_TASK_MODEL
    paginate_by = 8
    permission_classes = (IsProjectOwnerOrReadOnly,)
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

        qs = qs.exclude(status=BB_TASK_MODEL.TaskStatuses.closed)

        return qs

    def pre_save(self, obj):
        obj.author = self.request.user

class MyTaskList(generics.ListAPIView):
    model = BB_TASK_MODEL
    paginate_by = 8
    filter_fields = ('author',)
    serializer_class = MyTasksSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return BB_TASK_MODEL.objects.filter(author=self.request.user)
        return BB_TASK_MODEL.objects.none()


class TaskDetail(DefaultSerializerMixin, generics.RetrieveUpdateAPIView):
    model = BB_TASK_MODEL
    permission_classes = (IsAuthorOrReadOnly, )


class MyTaskDetail(DefaultSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    model = BB_TASK_MODEL
    permission_classes = (IsAuthorOrReadOnly, )


class TaskMemberList(generics.ListCreateAPIView):
    model = BB_TASKMEMBER_MODEL
    serializer_class = BaseTaskMemberSerializer
    paginate_by = 50
    filter_fields = ('task', 'status', )
    permission_classes = (IsAuthenticatedOrReadOnly, )
    queryset = model.objects.all()

    def pre_save(self, obj):
        # When creating a task member it should always be by the request.user and have status 'applied'
        obj.member = self.request.user
        obj.status = BB_TASKMEMBER_MODEL.TaskMemberStatuses.applied


class MyTaskMemberList(generics.ListAPIView):
    model = BB_TASKMEMBER_MODEL
    serializer_class = MyTaskMemberSerializer

    def get_queryset(self):
        queryset = super(MyTaskMemberList, self).get_queryset()
        # valid_statuses = [TaskMember.TaskMemberStatuses.accepted, TaskMember.TaskMemberStatuses.realized]
        return queryset.filter(member=self.request.user)#, status__in=valid_statuses)


class TaskMemberDetail(generics.RetrieveUpdateDestroyAPIView):
    model = BB_TASKMEMBER_MODEL
    serializer_class = BaseTaskMemberSerializer

    permission_classes = (IsMemberOrAuthorOrReadOnly, )
    

class TaskFileList(generics.ListCreateAPIView):
    model = BB_TASKFILE_MODEL
    serializer_class = TaskFileSerializer
    paginate_by = 50
    filter_fields = ('task', )
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def pre_save(self, obj):
        # When creating a task file the author should always be by the request.user
        obj.author = self.request.user


class TaskFileDetail(generics.RetrieveUpdateAPIView):
    model = BB_TASKFILE_MODEL
    serializer_class = TaskFileSerializer

    permission_classes = (IsAuthorOrReadOnly, )


class SkillList(generics.ListAPIView):
    model = BB_SKILL_MODEL
    serializer_class = SkillSerializer


class UsedSkillList(SkillList):
    def get_queryset(self):
        qs = super(UsedSkillList, self).get_queryset()
        skill_ids = BB_TASK_MODEL.objects.values_list('skill', flat=True).distinct()
        return qs.filter(id__in=skill_ids)
