from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

from bluebottle.bluebottle_drf2.serializers import PrimaryKeyGenericRelatedField, TagSerializer, FileSerializer, TaggableSerializerMixin
from bluebottle.bb_accounts.serializers import UserPreviewSerializer
from bluebottle.utils.serializers import MetaField
from bluebottle.bb_projects.serializers import ProjectPreviewSerializer
from bluebottle.wallposts.serializers import TextWallpostSerializer

from bluebottle.utils.model_dispatcher import get_task_model, get_taskmember_model, get_taskfile_model, \
    get_task_skill_model

BB_TASK_MODEL = get_task_model()
BB_TASKMEMBER_MODEL = get_taskmember_model()
BB_TASKFILE_MODEL = get_taskfile_model()
BB_SKILL_MODEL = get_task_skill_model()


class TaskPreviewSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer()
    project = ProjectPreviewSerializer()
    skill = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = BB_TASK_MODEL


class BaseTaskMemberSerializer(serializers.ModelSerializer):
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


class BaseTaskSerializer(TaggableSerializerMixin, serializers.ModelSerializer):
    members = BaseTaskMemberSerializer(many=True, source='members', read_only=True)
    files = TaskFileSerializer(many=True, source='files', read_only=True)
    project = serializers.SlugRelatedField(slug_field='slug')
    skill = serializers.PrimaryKeyRelatedField()
    author = UserPreviewSerializer()
    status = serializers.ChoiceField(choices=BB_TASK_MODEL.TaskStatuses.choices,
                                     default=BB_TASK_MODEL.TaskStatuses.open)
    tags = TagSerializer()

    meta_data = MetaField(
        title='get_meta_title',
        fb_title='get_fb_title',
        tweet='get_tweet',
        image_source='project__projectplan__image',
    )

    def validate_deadline(self, task, field):
        if task['project'].deadline and task['deadline'] > task['project'].deadline:
            raise serializers.ValidationError(
                _('The deadline must be before the project deadline')
            )

        return task

    class Meta:
        model = BB_TASK_MODEL
        fields = ('id', 'members', 'files', 'project', 'skill', 'author', 'status', 'tags', 'description',
                  'location', 'deadline', 'time_needed', 'title', 'people_needed', 'meta_data')


class MyTaskPreviewSerializer(serializers.ModelSerializer):
    project = ProjectPreviewSerializer()
    skill = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = BB_TASK_MODEL
        fields = ('id', 'title', 'skill', 'project', 'time_needed')


class MyTaskMemberSerializer(BaseTaskMemberSerializer):
    task = MyTaskPreviewSerializer()
    member = serializers.PrimaryKeyRelatedField()

    class Meta(BaseTaskMemberSerializer.Meta):
        fields = BaseTaskMemberSerializer.Meta.fields + ('time_spent',)

class MyTasksSerializer(BaseTaskSerializer):
    task = MyTaskPreviewSerializer()
    skill = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = BB_TASK_MODEL
        fields = ('id', 'title', 'skill', 'project', 'time_needed', 'status')

# Task Wallpost serializers

class TaskWallpostSerializer(TextWallpostSerializer):
    """ TextWallpostSerializer with task specific customizations. """

    url = serializers.HyperlinkedIdentityField(view_name='task-twallpost-detail')
    task = PrimaryKeyGenericRelatedField(BB_TASK_MODEL)

    class Meta(TextWallpostSerializer.Meta):
        # Add the project slug field.
        fields = TextWallpostSerializer.Meta.fields + ('task', )


class SkillSerializer(serializers.ModelSerializer):

    class Meta:
        model = BB_SKILL_MODEL
        fields = ('id', 'name')
