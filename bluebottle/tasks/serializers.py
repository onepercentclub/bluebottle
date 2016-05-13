from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

from bluebottle.bluebottle_drf2.serializers import (
    PrimaryKeyGenericRelatedField, TagSerializer, FileSerializer,
    TaggableSerializerMixin)
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.tasks.models import Task, TaskMember, TaskFile, Skill
from bluebottle.utils.serializers import MetaField
from bluebottle.projects.serializers import ProjectPreviewSerializer
from bluebottle.wallposts.serializers import TextWallpostSerializer
from bluebottle.projects.models import Project
from bluebottle.members.models import Member


class TaskPreviewSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer()
    project = ProjectPreviewSerializer()
    skill = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = Task


class BaseTaskMemberSerializer(serializers.ModelSerializer):
    member = UserPreviewSerializer()
    status = serializers.ChoiceField(
        choices=TaskMember.TaskMemberStatuses.choices,
        required=False, default=TaskMember.TaskMemberStatuses.applied)
    motivation = serializers.CharField(required=False)

    class Meta:
        model = TaskMember
        fields = ('id', 'member', 'status', 'created', 'motivation', 'task',
                  'externals')


class TaskFileSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer()
    file = FileSerializer()

    class Meta:
        model = TaskFile


class BaseTaskSerializer(TaggableSerializerMixin, serializers.ModelSerializer):
    members = BaseTaskMemberSerializer(many=True, source='members',
                                       read_only=True)
    files = TaskFileSerializer(many=True, source='files', read_only=True)
    project = serializers.SlugRelatedField(slug_field='slug',
                                           queryset=Project.objects)
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects)
    author = UserPreviewSerializer()
    status = serializers.ChoiceField(choices=Task.TaskStatuses.choices,
                                     default=Task.TaskStatuses.open)
    tags = TagSerializer()
    time_needed = serializers.DecimalField(min_value=0.0)

    meta_data = MetaField(
        title='get_meta_title',
        fb_title='get_fb_title',
        tweet='get_tweet',
        image_source='project__projectplan__image',
    )

    def validate_deadline(self, task, field):
        if task['project'].deadline \
                and task['deadline'] > task['project'].deadline:
            raise serializers.ValidationError(
                _('The deadline must be before the project deadline')
            )

        return task

    class Meta:
        model = Task
        fields = ('id', 'members', 'files', 'project', 'skill',
                  'author', 'status', 'tags', 'description',
                  'location', 'deadline', 'time_needed', 'title',
                  'people_needed', 'meta_data')


class MyTaskPreviewSerializer(serializers.ModelSerializer):
    project = ProjectPreviewSerializer()
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects)

    class Meta:
        model = Task
        fields = ('id', 'title', 'skill', 'project', 'time_needed')


class MyTaskMemberSerializer(BaseTaskMemberSerializer):
    task = MyTaskPreviewSerializer()
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects)

    class Meta(BaseTaskMemberSerializer.Meta):
        fields = BaseTaskMemberSerializer.Meta.fields + ('time_spent',)


class MyTasksSerializer(BaseTaskSerializer):
    task = MyTaskPreviewSerializer()
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects)

    class Meta:
        model = Task
        fields = ('id', 'title', 'skill', 'project', 'time_needed',
                  'people_needed', 'status', 'deadline', 'description',
                  'location')


# Task Wallpost serializers

class TaskWallpostSerializer(TextWallpostSerializer):
    """ TextWallpostSerializer with task specific customizations. """

    url = serializers.HyperlinkedIdentityField(
        view_name='task-twallpost-detail')
    task = PrimaryKeyGenericRelatedField(Task, queryset=Task.objects)

    class Meta(TextWallpostSerializer.Meta):
        # Add the project slug field.
        fields = TextWallpostSerializer.Meta.fields + ('task',)


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name')
