from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import PrimaryKeyGenericRelatedField, TagSerializer, FileSerializer, TaggableSerializerMixin
from bluebottle.bb_accounts.serializers import UserPreviewSerializer
from bluebottle.utils.serializers import MetaField, HumanReadableChoiceField
from bluebottle.bb_projects.serializers import ProjectPreviewSerializer
from bluebottle.wallposts.serializers import TextWallPostSerializer

from . import get_task_model
from .models import TaskMember, TaskFile, Skill

BB_TASK_MODEL = get_task_model()


class TaskPreviewSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer()
    project = ProjectPreviewSerializer()
    skill = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = BB_TASK_MODEL
        fields = ('id', 'title', 'description', 'location', 'skill', 'status', 'created', 'project', 'deadline', 'time_needed')


class TaskMemberSerializer(serializers.ModelSerializer):
    member = UserPreviewSerializer()
    task = serializers.PrimaryKeyRelatedField()
    status = serializers.ChoiceField(choices=TaskMember.TaskMemberStatuses.choices, required=False, default=TaskMember.TaskMemberStatuses.applied)
    motivation = serializers.CharField(required=False)

    class Meta:
        model = TaskMember
        fields = ('id', 'member', 'task', 'status', 'created', 'motivation')


class TaskFileSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer()
    task = serializers.PrimaryKeyRelatedField()
    file = FileSerializer()

    class Meta:
        model = TaskFile
        fields = ('id', 'author', 'task', 'file', 'created', 'title')


class TaskSerializer(TaggableSerializerMixin, serializers.ModelSerializer):
    # members = TaskMemberSerializer(many=True, source='members', read_only=True)
    # files = TaskFileSerializer(many=True, source='files', read_only=True)
    project = serializers.SlugRelatedField(slug_field='slug')
    skill = serializers.PrimaryKeyRelatedField()
    author = UserPreviewSerializer()
    status = HumanReadableChoiceField(choices=BB_TASK_MODEL.TaskStatuses.choices, default=BB_TASK_MODEL.TaskStatuses.open)

    tags = TagSerializer()
    meta_data = MetaField(
        title = 'get_meta_title',
        fb_title = 'get_fb_title',
        tweet = 'get_tweet',
        image_source = 'project__projectplan__image',
        )

    class Meta:
        model = BB_TASK_MODEL
        fields = ('id', 'title', 'project', 'description', 'end_goal', 'members', 'files', 'location', 'skill',
                  'time_needed', 'author', 'status', 'created', 'deadline', 'tags', 'meta_data',
                  'people_needed'
        )


class SkillSerializer(serializers.ModelSerializer):

    class Meta:
        model = Skill
        fields = ('id', 'name')

class MyTaskPreviewSerializer(serializers.ModelSerializer):
    project = ProjectPreviewSerializer()
    skill = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = BB_TASK_MODEL
        fields = ('id', 'title', 'skill', 'project', 'time_needed')


class MyTaskMemberSerializer(TaskMemberSerializer):
    task = MyTaskPreviewSerializer()
    member = serializers.PrimaryKeyRelatedField()

    class Meta(TaskMemberSerializer.Meta):
        fields = TaskMemberSerializer.Meta.fields + ('time_spent',)


# Task WallPost serializers

class TaskWallPostSerializer(TextWallPostSerializer):
    """ TextWallPostSerializer with task specific customizations. """

    url = serializers.HyperlinkedIdentityField(view_name='task-twallpost-detail')
    task = PrimaryKeyGenericRelatedField(BB_TASK_MODEL)

    class Meta(TextWallPostSerializer.Meta):
        # Add the project slug field.
        fields = TextWallPostSerializer.Meta.fields + ('task', )


