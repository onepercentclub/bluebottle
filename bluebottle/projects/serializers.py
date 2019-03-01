from django.utils import timezone
from django.utils.translation import ugettext as _

from rest_framework import serializers

from bluebottle.bb_projects.models import ProjectTheme, ProjectPhase
from bluebottle.bluebottle_drf2.serializers import (
    OEmbedField, SorlImageField, ImageSerializer,
    PrivateFileSerializer
)
from bluebottle.categories.models import Category
from bluebottle.donations.models import Donation
from bluebottle.geo.models import Country, Location
from bluebottle.geo.serializers import CountrySerializer, PlaceSerializer
from bluebottle.members.serializers import UserProfileSerializer, UserPreviewSerializer
from bluebottle.organizations.serializers import OrganizationPreviewSerializer
from bluebottle.payouts.serializers import PayoutAccountSerializer
from bluebottle.projects.models import (
    ProjectBudgetLine, Project, ProjectImage,
    ProjectPlatformSettings, ProjectSearchFilter, ProjectLocation,
    ProjectAddOn, ProjectCreateTemplate)
from bluebottle.tasks.models import Task, TaskMember, Skill
from bluebottle.utils.serializers import (
    MoneySerializer, ResourcePermissionField,
    RelatedResourcePermissionField,
)
from bluebottle.utils.fields import SafeField
from bluebottle.projects.permissions import (
    CanExportSupportersPermission
)
from bluebottle.utils.utils import get_class
from bluebottle.wallposts.models import MediaWallpostPhoto, MediaWallpost, TextWallpost
from bluebottle.votes.models import Vote


class ProjectPhaseLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase


class ProjectPhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase

        fields = ('id', 'slug', 'name', 'description', 'sequence', 'active', 'editable', 'viewable', 'owner_editable', )


class ProjectThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectTheme
        fields = ('id', 'name', 'description')


class ProjectCountrySerializer(CountrySerializer):
    subregion = serializers.CharField(source='subregion.name')

    class Meta:
        model = Country
        fields = ('id', 'name', 'subregion', 'code')


class ProjectLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectLocation
        fields = (
            'street', 'country', 'city', 'neighborhood', 'latitude', 'longitude'
        )


class ProjectBudgetLineSerializer(serializers.ModelSerializer):
    amount = MoneySerializer()
    project = serializers.SlugRelatedField(slug_field='slug', queryset=Project.objects)

    class Meta:
        model = ProjectBudgetLine
        fields = ('id', 'project', 'description', 'amount')


class BasicProjectBudgetLineSerializer(serializers.ModelSerializer):
    amount = MoneySerializer()

    class Meta:
        model = ProjectBudgetLine
        fields = ('id', 'description', 'amount')


class ProjectPermissionsSerializer(serializers.Serializer):
    def get_attribute(self, obj):
        return obj

    rewards = RelatedResourcePermissionField('reward-list')
    donations = RelatedResourcePermissionField('order-manage-list')
    tasks = RelatedResourcePermissionField('task-list')
    manage_project = RelatedResourcePermissionField('project_manage_detail', view_args=('slug', ))

    class Meta:
        fields = ('rewards', 'donations', 'tasks', 'manage_project')


class BaseProjectAddOnSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectAddOn
        fields = ('id', 'type')


class ProjectAddOnSerializer(serializers.ModelSerializer):

    type = serializers.ReadOnlyField(required=False)

    def to_representation(self, obj):
        """
        Project Add On Polymorphic serialization
        """
        AddOnSerializer = get_class(obj.serializer)
        return AddOnSerializer(obj, context=self.context).to_representation(obj)

    class Meta:
        model = ProjectAddOn
        fields = ('id', 'type')


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    addons = ProjectAddOnSerializer(many=True)
    amount_asked = MoneySerializer()
    amount_donated = MoneySerializer()
    amount_extra = MoneySerializer()
    amount_needed = MoneySerializer()
    amount_cancelled = MoneySerializer(read_only=True)
    budget_lines = BasicProjectBudgetLineSerializer(many=True, source='projectbudgetline_set', read_only=True)
    categories = serializers.SlugRelatedField(slug_field='slug', many=True, queryset=Category.objects)
    country = ProjectCountrySerializer()
    currencies = serializers.JSONField(read_only=True)
    has_voted = serializers.SerializerMethodField()
    image = ImageSerializer(required=False)
    is_funding = serializers.ReadOnlyField()
    location = serializers.PrimaryKeyRelatedField(required=False, queryset=Location.objects)
    organization = OrganizationPreviewSerializer(read_only=True)
    owner = UserProfileSerializer()
    people_needed = serializers.ReadOnlyField()
    people_registered = serializers.ReadOnlyField()
    permissions = ResourcePermissionField('project_detail', view_args=('slug',))
    promoter = UserProfileSerializer(read_only=True)
    related_permissions = ProjectPermissionsSerializer(read_only=True)
    story = SafeField()
    supporter_count = serializers.IntegerField()
    task_manager = UserProfileSerializer(read_only=True)
    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')
    vote_count = serializers.IntegerField()
    latitude = serializers.FloatField(source='projectlocation.latitude')
    longitude = serializers.FloatField(source='projectlocation.longitude')
    project_location = ProjectLocationSerializer(read_only=True, source='projectlocation')
    supporters_export_url = PrivateFileSerializer(
        'project-supporters-export', url_args=('slug', ), permission=CanExportSupportersPermission,
        read_only=True
    )

    def __init__(self, *args, **kwargs):
        super(ProjectSerializer, self).__init__(*args, **kwargs)

    def get_has_voted(self, obj):
        return Vote.has_voted(self.context['request'].user, obj)

    class Meta:
        model = Project
        fields = ('id',
                  'addons',
                  'allow_overfunding',
                  'amount_asked',
                  'amount_donated',
                  'amount_extra',
                  'amount_needed',
                  'amount_cancelled',
                  'budget_lines',
                  'categories',
                  'celebrate_results',
                  'country',
                  'created',
                  'currencies',
                  'deadline',
                  'campaign_duration',
                  'description',
                  'full_task_count',
                  'has_voted',
                  'image',
                  'is_funding',
                  'latitude',
                  'location',
                  'longitude',
                  'project_location',
                  'open_task_count',
                  'organization',
                  'owner',
                  'people_needed',
                  'people_registered',
                  'permissions',
                  'pitch',
                  'place',
                  'project_type',
                  'promoter',
                  'realized_task_count',
                  'related_permissions',
                  'status',
                  'status',
                  'story',
                  'supporter_count',
                  'task_count',
                  'task_manager',
                  'theme',
                  'title',
                  'video_html',
                  'video_url',
                  'vote_count',
                  'voting_deadline',
                  'supporters_export_url',
                  )


class ProjectPreviewSerializer(ProjectSerializer):
    categories = serializers.SlugRelatedField(many=True, read_only=True, slug_field='slug')
    image = ImageSerializer(required=False)
    owner = UserProfileSerializer()
    skills = serializers.SerializerMethodField()
    project_location = ProjectLocationSerializer(read_only=True, source='projectlocation')
    theme = ProjectThemeSerializer()

    def get_skills(self, obj):
        return set(task.skill.id for task in obj.task_set.all() if task.skill)

    class Meta:
        model = Project
        fields = ('id',
                  'allow_overfunding',
                  'amount_asked',
                  'amount_donated',
                  'amount_extra',
                  'amount_needed',
                  'amount_cancelled',
                  'categories',
                  'celebrate_results',
                  'country',
                  'deadline',
                  'campaign_duration',
                  'full_task_count',
                  'image',
                  'is_campaign',
                  'is_funding',
                  'latitude',
                  'location',
                  'project_location',
                  'longitude',
                  'open_task_count',
                  'owner',
                  'people_needed',
                  'people_registered',
                  'pitch',
                  'place',
                  'project_type',
                  'realized_task_count',
                  'skills',
                  'status',
                  'task_count',
                  'theme',
                  'title',
                  'vote_count',
                  'voting_deadline',
                  )


class ProjectTinyPreviewSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    image = SorlImageField('400x300', crop='center')
    latitude = serializers.FloatField(source='projectlocation.latitude')
    longitude = serializers.FloatField(source='projectlocation.longitude')

    class Meta:
        model = Project
        fields = ('id', 'title', 'slug', 'status', 'image', 'latitude', 'longitude')


class ManageTaskSerializer(serializers.ModelSerializer):
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects)
    time_needed = serializers.DecimalField(min_value=0.0, max_digits=5, decimal_places=2)
    place = PlaceSerializer(required=False)

    class Meta:
        model = Task
        fields = ('id',
                  'deadline',
                  'description',
                  'location',
                  'people_needed',
                  'skill',
                  'time_needed',
                  'title',
                  'place',
                  'type',)


class ManageProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)

    amount_asked = MoneySerializer(required=False, allow_null=True)
    amount_donated = MoneySerializer(read_only=True)
    amount_needed = MoneySerializer(read_only=True)
    amount_cancelled = MoneySerializer(read_only=True)
    budget_lines = ProjectBudgetLineSerializer(many=True, source='projectbudgetline_set', read_only=True)
    currencies = serializers.JSONField(read_only=True)
    categories = serializers.SlugRelatedField(many=True, read_only=True, slug_field='slug')
    editable = serializers.BooleanField(read_only=True)
    image = ImageSerializer(required=False, allow_null=True)
    is_funding = serializers.ReadOnlyField()
    location = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=Location.objects)
    payout_account = PayoutAccountSerializer(required=False, allow_null=True)
    people_needed = serializers.IntegerField(read_only=True)
    people_registered = serializers.IntegerField(read_only=True)
    pitch = serializers.CharField(required=False, allow_null=True)
    promoter = UserProfileSerializer(read_only=True)
    slug = serializers.CharField(read_only=True)
    status = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=ProjectPhase.objects)
    story = SafeField(required=False, allow_blank=True)
    task_manager = UserProfileSerializer(read_only=True)
    owner = UserProfileSerializer(read_only=True)
    tasks = ManageTaskSerializer(many=True, source='task_set', read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name='project_manage_detail', lookup_field='slug')
    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')
    viewable = serializers.BooleanField(read_only=True)
    permissions = ResourcePermissionField('project_manage_detail', view_args=('slug', ))
    related_permissions = ProjectPermissionsSerializer(read_only=True)

    latitude = serializers.FloatField(source='projectlocation.latitude', required=False, allow_null=True)
    longitude = serializers.FloatField(source='projectlocation.longitude', required=False, allow_null=True)
    project_location = ProjectLocationSerializer(read_only=True, source='projectlocation')

    editable_fields = ('pitch', 'story', 'image', 'video_url', 'projectlocation')

    def validate_status(self, value):
        if not value:
            value = ProjectPhase.objects.order_by('sequence').all()[0]
        else:
            """
            Don't let the owner set a status with a sequence number higher
            than 2
            They can set 1: plan-new or 2: plan-submitted

            TODO: This needs work. Maybe we could use a FSM for the project
                  status
                  transitions, e.g.:
                      https://pypi.python.org/pypi/django-fsm/1.2.0

            TODO: what to do if the expected status (plan-submitted) is
                  not found?! Hard fail?
            """
            submit_status = ProjectPhase.objects.get(slug='plan-submitted')
            new_status = ProjectPhase.objects.get(slug='plan-new')
            needs_work_status = ProjectPhase.objects.get(
                slug='plan-needs-work')

            proposed_status = value
            current_status = None

            # Get the current status or the first if not found
            try:
                current_status = Project.objects.get(slug=self.initial_data['slug']).status
            except (Project.DoesNotExist, KeyError):
                current_status = ProjectPhase.objects.order_by(
                    'sequence').all()[0]

            if current_status and proposed_status:
                """
                These are possible combinations of current v. proposed status
                which are permitted:
                1) the current status is the same as the proposed status
                2) the current is new or needs work and the proposed
                   is submitted
                """
                if proposed_status == current_status:
                    return value
                if proposed_status != submit_status or current_status not in [new_status, needs_work_status]:
                    raise serializers.ValidationError(_("You can not change the project state."))
        return value

    def validate(self, data):
        if self.instance and self.instance.status.slug in ('campaign', 'voting'):
            # When project is running, only a subset of the fields canb be changed
            for field, value in data.items():
                current = getattr(self.instance, field)

                if field not in self.editable_fields:
                    try:
                        # If we check a many to many field, make convert both sides to a set
                        current = set(current.all())
                        value = set(value)
                    except (AttributeError, TypeError):
                        # normal field: do nothing
                        pass

                    if value != current:
                        raise serializers.ValidationError(
                            _('Not allowed to edit {} when project is running').format(field)
                        )
                self.instance.campaign_edited = timezone.now()

        return data

    def update(self, instance, validated_data):
        if 'projectlocation' in validated_data:
            location = validated_data.pop('projectlocation')

            for field, value in location.items():
                setattr(instance.projectlocation, field, value)
            instance.projectlocation.save()

        if 'payout_account' in validated_data:
            validated_data.pop('payout_account')
            serializer = PayoutAccountSerializer(
                data=self.initial_data['payout_account'],
                instance=instance.payout_account
            )
            if serializer.is_valid():
                serializer.validated_data['user'] = self.context['request'].user
                instance.payout_account = serializer.save()

        return super(ManageProjectSerializer, self).update(instance, validated_data)

    def create(self, validated_data):
        location_data = None
        if 'projectlocation' in validated_data:
            location_data = validated_data.pop('projectlocation')

        instance = super(ManageProjectSerializer, self).create(validated_data)
        if location_data:
            for field, value in location_data.items():
                setattr(instance.projectlocation, field, value)

            instance.projectlocation.save()

        return instance

    class Meta:
        model = Project
        fields = ('id',
                  'amount_asked',
                  'amount_donated',
                  'amount_needed',
                  'amount_cancelled',
                  'budget_lines',
                  'categories',
                  'country',
                  'created',
                  'currencies',
                  'deadline',
                  'campaign_duration',
                  'description',
                  'editable',
                  'image',
                  'is_funding',
                  'latitude',
                  'location',
                  'longitude',
                  'organization',
                  'payout_account',
                  'people_needed',
                  'people_registered',
                  'pitch',
                  'place',
                  'project_location',
                  'project_type',
                  'promoter',
                  'slug',
                  'status',
                  'story',
                  'task_manager',
                  'owner',
                  'tasks',
                  'theme',
                  'title',
                  'url',
                  'video_html',
                  'video_url',
                  'permissions',
                  'related_permissions',
                  'viewable',)


class ProjectDonationSerializer(serializers.ModelSerializer):
    member = UserPreviewSerializer(source='user')
    date_donated = serializers.DateTimeField(source='ready')
    amount = MoneySerializer()
    siblings = serializers.IntegerField()

    class Meta:
        model = Donation
        fields = ('member', 'date_donated', 'amount',)


class ProjectWallpostPhotoSerializer(serializers.ModelSerializer):
    photo = ImageSerializer(read_only=True)
    created = serializers.DateTimeField(source='mediawallpost.created', read_only=True)

    class Meta:
        model = MediaWallpostPhoto
        fields = ('id', 'photo', 'created', 'results_page')


class ProjectWallpostVideoSerializer(serializers.ModelSerializer):
    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')
    video_url = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = MediaWallpost
        fields = ('id', 'video_url', 'video_html', 'created')


class ProjectMediaSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug')
    image = SorlImageField('1200x600', crop='center',
                           watermark='images/completed.png',
                           watermark_pos='-40 40',
                           watermark_size='213x255')
    pictures = ProjectWallpostPhotoSerializer(source='wallpost_photos', many=True)
    videos = ProjectWallpostVideoSerializer(source='wallpost_videos', many=True)

    class Meta:
        model = Project
        fields = ('id', 'title', 'pictures', 'videos', 'image')


class ProjectDonorSerializer(serializers.ModelSerializer):
    """
    Members that made a donation
    """
    user = UserPreviewSerializer()

    class Meta:
        model = Donation
        fields = ('id', 'user', 'created')


class ProjectTaskMemberSerializer(serializers.ModelSerializer):
    """
    Members that joined a task
    """
    user = UserPreviewSerializer(source='member')

    class Meta:
        model = TaskMember
        fields = ('id', 'user', 'created', 'motivation', 'task')


class ProjectPosterSerializer(serializers.ModelSerializer):
    """
    Members that wrote a wallpost
    """
    user = UserPreviewSerializer(source='author')

    class Meta:
        model = TextWallpost
        fields = ('id', 'user', 'created', 'text')


class ProjectSupportSerializer(serializers.ModelSerializer):
    """
    Lists with different project supporter types
    """

    id = serializers.CharField(source='slug')
    donors = ProjectDonorSerializer(many=True)
    posters = ProjectPosterSerializer(many=True)
    task_members = ProjectTaskMemberSerializer(many=True)

    class Meta:
        model = Project
        fields = ('id', 'title', 'donors', 'task_members', 'posters')


class ProjectImageSerializer(serializers.ModelSerializer):
    """
    Members that wrote a wallpost
    """
    image = ImageSerializer(source='file')
    project = serializers.SlugRelatedField(slug_field='slug', queryset=Project.objects)

    class Meta:
        model = ProjectImage
        fields = ('id', 'image', 'project')


class ProjectSearchFilterSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectSearchFilter
        fields = (
            'name',
            'default',
            'values',
            'sequence'
        )


class ProjectCreateTemplateSerializer(serializers.ModelSerializer):
    default_amount_asked = MoneySerializer(min_amount=5.0)
    image = ImageSerializer()
    default_image = ImageSerializer()
    default_story = serializers.CharField(source='default_description')

    class Meta:
        model = ProjectCreateTemplate
        fields = (
            'name',
            'sub_name',
            'image',
            'description',

            'default_amount_asked',
            'default_title',
            'default_pitch',
            'default_story',
            'default_image',
        )


class ProjectPlatformSettingsSerializer(serializers.ModelSerializer):

    filters = ProjectSearchFilterSerializer(many=True)
    templates = ProjectCreateTemplateSerializer(many=True)

    class Meta:
        model = ProjectPlatformSettings
        fields = (
            'create_types',
            'create_flow',
            'contact_method',
            'contact_types',
            'match_options',
            'share_options',
            'facebook_at_work_url',
            'filters',
            'templates',
            'allow_anonymous_rewards'
        )
