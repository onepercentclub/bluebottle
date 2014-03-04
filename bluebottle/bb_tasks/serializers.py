from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import PrimaryKeyGenericRelatedField, TagSerializer, FileSerializer, TaggableSerializerMixin
from bluebottle.bb_accounts.serializers import UserPreviewSerializer
from bluebottle.utils.serializers import MetaField, HumanReadableChoiceField
from bluebottle.bb_projects.serializers import ProjectPreviewSerializer
from bluebottle.wallposts.serializers import TextWallPostSerializer

from bluebottle.utils.utils import get_task_model, get_taskmember_model, get_taskfile_model, get_skill_model

BB_TASK_MODEL = get_task_model()
BB_TASKMEMBER_MODEL = get_taskmember_model()
BB_TASKFILE_MODEL = get_taskfile_model()
BB_SKILL_MODEL = get_skill_model

class TaskPreviewSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer()
    project = ProjectPreviewSerializer()
    skill = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = BB_TASK_MODEL


class TaskMemberSerializer(serializers.ModelSerializer):
    member = UserPreviewSerializer()
    status = serializers.ChoiceField(
        choices=BB_TASKMEMBER_MODEL.TaskMemberStatuses.choices,
        required=False, default=BB_TASKMEMBER_MODEL.TaskMemberStatuses.applied)
    motivation = serializers.CharField(required=False)

    class Meta:
        model = BB_TASKMEMBER_MODEL
        fields = ('id', 'member', 'status', 'created', 'motivation', 'task')


class TaskFileSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer()
    file = FileSerializer()

    class Meta:
        model = BB_TASKFILE_MODEL


class TaskSerializer(serializers.ModelSerializer):
    members = TaskMemberSerializer(many=True, source='members', read_only=True)
    files = TaskFileSerializer(many=True, source='files', read_only=True)
    project = serializers.SlugRelatedField(slug_field='slug')
    skill = serializers.PrimaryKeyRelatedField()
    author = UserPreviewSerializer()
    status = HumanReadableChoiceField(
        choices=BB_TASK_MODEL.TaskStatuses.choices, default=BB_TASK_MODEL.TaskStatuses.open)
    tags = TagSerializer()

    meta_data = MetaField(
        title='get_meta_title',
        fb_title='get_fb_title',
        tweet='get_tweet',
        image_source='project__projectplan__image',
    )

    class Meta:
        model = BB_TASK_MODEL


class MyTaskPreviewSerializer(serializers.ModelSerializer):
    project = ProjectPreviewSerializer()
    skill = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = BB_TASK_MODEL
        fields = ('id', 'title', 'skill', 'project', 'time_needed', 'end_goal')


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
