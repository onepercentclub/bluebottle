from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

from bluebottle.bluebottle_drf2.serializers import (
    PrimaryKeyGenericRelatedField, FileSerializer, PrivateFileSerializer
)
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.tasks.models import Task, TaskMember, TaskFile, Skill
from bluebottle.projects.serializers import ProjectPreviewSerializer
from bluebottle.wallposts.serializers import TextWallpostSerializer
from bluebottle.projects.models import Project
from bluebottle.members.models import Member


class BaseTaskMemberSerializer(serializers.ModelSerializer):
    member = UserPreviewSerializer()
    status = serializers.ChoiceField(
        choices=TaskMember.TaskMemberStatuses.choices,
        required=False, default=TaskMember.TaskMemberStatuses.applied)
    motivation = serializers.CharField(required=False)
    resume = PrivateFileSerializer(
        url_name='task-member-resume', required=False
    )

    class Meta:
        model = TaskMember
        fields = ('id', 'member', 'status', 'created', 'motivation', 'task',
                  'externals', 'time_spent', 'resume')


class TaskFileSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer()
    file = FileSerializer()

    class Meta:
        model = TaskFile


class BaseTaskSerializer(serializers.ModelSerializer):
    members = BaseTaskMemberSerializer(many=True, read_only=True, source='members_applied')
    files = TaskFileSerializer(many=True, read_only=True)
    project = serializers.SlugRelatedField(slug_field='slug',
                                           queryset=Project.objects)
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects)
    author = UserPreviewSerializer()
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
        fields = ('id', 'members', 'files', 'project', 'skill',
                  'author', 'status', 'description', 'type', 'accepting',
                  'location', 'deadline', 'deadline_to_apply',
                  'time_needed', 'title', 'people_needed')


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
        fields = ('id', 'title', 'skill', 'project', 'time_needed',
                  'people_needed', 'status', 'deadline', 'deadline_to_apply',
                  'accepting', 'description', 'location', 'type')


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
