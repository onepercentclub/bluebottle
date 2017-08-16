from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

from bluebottle.bluebottle_drf2.serializers import (
    PrimaryKeyGenericRelatedField, FileSerializer, PrivateFileSerializer
)
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.tasks.models import Task, TaskMember, TaskFile, Skill
from bluebottle.projects.serializers import ProjectPreviewSerializer
from bluebottle.utils.serializers import RelatedPermissionField, PermissionField
from bluebottle.wallposts.serializers import TextWallpostSerializer
from bluebottle.projects.models import Project
from bluebottle.members.models import Member


class BaseTaskMemberSerializer(serializers.ModelSerializer):
    member = UserPreviewSerializer()
    status = serializers.ChoiceField(
        choices=TaskMember.TaskMemberStatuses.choices,
        required=False, default=TaskMember.TaskMemberStatuses.applied)
    motivation = serializers.CharField(required=False, allow_blank=True)
    resume = PrivateFileSerializer(
        url_name='task-member-resume', required=False, allow_null=True
    )

    class Meta:
        model = TaskMember
        fields = ('id', 'member', 'status', 'created', 'motivation', 'task',
                  'externals', 'time_spent', 'resume')

    def to_representation(self, obj):
        ret = super(BaseTaskMemberSerializer, self).to_representation(obj)
        if self.context['request'].method == 'GET' \
                and self.context['request'].user not in [obj.member, obj.task.author, obj.task.project.owner]:
            ret['motivation'] = ''
        return ret


class TaskFileSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer()
    file = FileSerializer()

    class Meta:
        model = TaskFile


class TaskPermissionsSerializer(serializers.Serializer):
    def get_attribute(self, obj):
        return obj

    task_members = RelatedPermissionField('task-member-list', data_mappings={'task': 'id'})

    class Meta:
        fields = ('task_members', )


class BaseTaskSerializer(serializers.ModelSerializer):
    members = BaseTaskMemberSerializer(many=True, read_only=True, source='members_applied')
    files = TaskFileSerializer(many=True, read_only=True)
    project = serializers.SlugRelatedField(slug_field='slug',
                                           queryset=Project.objects)
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects)
    author = UserPreviewSerializer()
    permissions = PermissionField('task_detail', view_args=('id',))
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

        if not data['deadline'] or data['deadline'] > data['project'].deadline:
            raise serializers.ValidationError(
                {'deadline': [_("The deadline must be before the project deadline.")]}
            )

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
    name = serializers.CharField(source='localized_name')

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
