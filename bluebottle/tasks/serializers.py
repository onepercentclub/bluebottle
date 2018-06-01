from datetime import timedelta
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from bluebottle.bluebottle_drf2.serializers import (
    PrimaryKeyGenericRelatedField, FileSerializer, PrivateFileSerializer
)
from bluebottle.members.serializers import UserPreviewSerializer, UserProfileSerializer
from bluebottle.tasks.models import Task, TaskMember, TaskFile, Skill
from bluebottle.tasks.permissions import TaskMemberPermission, TaskManagerPermission
from bluebottle.tasks.taskmail import TaskMemberMailAdapter
from bluebottle.projects.serializers import ProjectPreviewSerializer
from bluebottle.utils.permissions import OneOf
from bluebottle.utils.serializers import PermissionField, ResourcePermissionField
from bluebottle.wallposts.serializers import TextWallpostSerializer
from bluebottle.projects.models import Project
from bluebottle.members.models import Member


class UniqueTaskMemberValidator(object):
    def set_context(self, serializer):
        self.instance = serializer.instance
        self.request = serializer.context['request']

    def __call__(self, data):
        if self.instance is None:
            queryset = TaskMember.objects.filter(
                member=self.request.user,
                task=data['task']
            ).exclude(
                status__in=(
                    TaskMember.TaskMemberStatuses.rejected,
                    TaskMember.TaskMemberStatuses.withdrew
                )
            )

            if queryset.exists():
                raise ValidationError(
                    _('It is not possible to apply twice for the same task')
                )


class BaseTaskMemberSerializer(serializers.ModelSerializer):
    member = UserPreviewSerializer()
    status = serializers.ChoiceField(
        choices=TaskMember.TaskMemberStatuses.choices,
        required=False, default=TaskMember.TaskMemberStatuses.applied)
    motivation = serializers.CharField(required=False, allow_blank=True)
    resume = PrivateFileSerializer(
        url_name='task-member-resume', url_args=('pk', ), file_attr='resume',
        required=False, allow_null=True,
        permission=OneOf(TaskManagerPermission, TaskMemberPermission)
    )
    permissions = ResourcePermissionField('task-member-detail', view_args=('id',))

    class Meta:
        model = TaskMember
        fields = ('id', 'member', 'status', 'created', 'motivation', 'task',
                  'externals', 'time_spent', 'resume', 'permissions')
        validators = (UniqueTaskMemberValidator(), )

    def validate(self, data):
        if 'time_spent' not in data or not self.instance:
            return data

        if (
            self.instance.time_spent != data['time_spent'] and
            self.context['request'].user == self.instance.member and
            self.instance.project.task_manager != self.instance.member
        ):
            raise serializers.ValidationError('User can not update their own time spent')

        return data

    def to_representation(self, obj):
        ret = super(BaseTaskMemberSerializer, self).to_representation(obj)
        if self.context['request'].method == 'GET' \
                and self.context['request'].user not in [obj.member, obj.task.author, obj.task.project.owner]:
            ret['motivation'] = ''
        return ret


class TaskMemberStatusSerializer(serializers.ModelSerializer):
    member = UserPreviewSerializer(read_only=True)
    permissions = ResourcePermissionField('task-member-status', view_args=('id',))
    message = serializers.CharField(write_only=True)

    class Meta:
        model = TaskMember
        fields = ('id', 'member', 'status', 'permissions', 'message')

    def update(self, instance, validated_data):
        message = validated_data.pop('message')
        instance.skip_mail = True

        result = super(TaskMemberStatusSerializer, self).update(instance, validated_data)

        if instance._original_status != instance.status:
            TaskMemberMailAdapter(self.instance, message=message).send_mail()

        return result


class TaskFileSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer()
    file = FileSerializer()

    class Meta:
        model = TaskFile


class TaskPermissionsSerializer(serializers.Serializer):
    def get_attribute(self, obj):
        return obj

    task_members = PermissionField('task-member-list')

    class Meta:
        fields = ('task_members', )


class BaseTaskSerializer(serializers.ModelSerializer):
    members = BaseTaskMemberSerializer(many=True, read_only=True)
    files = TaskFileSerializer(many=True, read_only=True)
    project = serializers.SlugRelatedField(slug_field='slug',
                                           queryset=Project.objects)
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects)
    author = UserProfileSerializer(read_only=True)
    permissions = ResourcePermissionField('task_detail', view_args=('id',))
    related_permissions = TaskPermissionsSerializer(read_only=True)
    status = serializers.ChoiceField(choices=Task.TaskStatuses.choices,
                                     default=Task.TaskStatuses.open)
    time_needed = serializers.DecimalField(min_value=0.0,
                                           max_digits=5,
                                           decimal_places=2)

    def validate(self, data):
        if self.instance and data.get('deadline') and self.instance.deadline.date() == data['deadline'].date():
            # The date has not changed: Do not validate
            return data

        project_deadline = data['project'].deadline
        project_is_funding = data['project'].project_type in ['funding', 'both']
        if data.get('deadline') > project_deadline and project_is_funding:
            raise serializers.ValidationError({
                'deadline': [
                    _("The deadline can not be more than the project deadline")
                ]
            })

        project_started = data['project'].campaign_started or data['project'].created
        if data.get('deadline') > project_started + timedelta(days=366):
            raise serializers.ValidationError({
                'deadline': [
                    _("The deadline can not be more than a year after the project started")
                ]
            })

        if not data['deadline_to_apply'] or data['deadline_to_apply'] > data['deadline']:
            raise serializers.ValidationError(
                {'deadline': [_("The deadline to apply must be before the deadline.")]}
            )

        return data

    class Meta:
        model = Task
        fields = (
            'accepting',
            'author',
            'deadline',
            'deadline_to_apply',
            'description',
            'files',
            'id',
            'location',
            'members',
            'needs_motivation',
            'people_needed',
            'permissions',
            'project',
            'related_permissions',
            'skill',
            'status',
            'time_needed',
            'title',
            'type',
        )

    def _check_project_deadline(self, instance, validated_data):
        project = validated_data['project']
        if instance.deadline > project.deadline:
            project.deadline = instance.deadline
            project.save()

    def create(self, validated_data):
        instance = super(BaseTaskSerializer, self).create(validated_data)
        self._check_project_deadline(instance, validated_data)
        return instance

    def update(self, instance, validated_data):
        result = super(BaseTaskSerializer, self).update(instance, validated_data)
        self._check_project_deadline(instance, validated_data)
        return result


class MyTaskPreviewSerializer(serializers.ModelSerializer):
    project = ProjectPreviewSerializer()
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects)

    class Meta:
        model = Task
        fields = ('id', 'title', 'skill', 'project', 'time_needed', 'type')


class MyTaskMemberSerializer(BaseTaskMemberSerializer):
    task = MyTaskPreviewSerializer()
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects)


class MyTasksSerializer(BaseTaskSerializer):
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects)

    class Meta:
        model = Task
        fields = (
            'accepting',
            'deadline',
            'deadline_to_apply',
            'description',
            'id',
            'location',
            'needs_motivation',
            'people_needed',
            'permissions',
            'project',
            'related_permissions',
            'skill',
            'status',
            'time_needed',
            'title',
            'type'
        )


# Task Wallpost serializers

class TaskWallpostSerializer(TextWallpostSerializer):
    """ TextWallpostSerializer with task specific customizations. """

    url = serializers.HyperlinkedIdentityField(
        view_name='task-twallpost-detail', lookup_field='pk')
    task = PrimaryKeyGenericRelatedField(Task)

    class Meta(TextWallpostSerializer.Meta):
        # Add the project slug field.
        fields = TextWallpostSerializer.Meta.fields + ('task',)


class SkillSerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta:
        model = Skill
        fields = ('id', 'name', 'expertise')


class TaskPreviewSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer()
    project = ProjectPreviewSerializer()
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill)
    members = BaseTaskMemberSerializer(many=True, read_only=True, source="members_applied")

    class Meta:
        model = Task
        fields = '__all__'
