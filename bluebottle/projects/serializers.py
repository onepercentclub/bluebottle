import re
from django.utils.translation import ugettext as _

from rest_framework import serializers
from localflavor.generic.validators import IBANValidator

from bluebottle.bb_projects.models import ProjectTheme, ProjectPhase
from bluebottle.bluebottle_drf2.serializers import (
    OEmbedField, SorlImageField, ImageSerializer,
    PrivateFileSerializer
)
from bluebottle.bb_projects.permissions import ProjectPermissions
from bluebottle.categories.models import Category
from bluebottle.donations.models import Donation
from bluebottle.geo.models import Country, Location
from bluebottle.geo.serializers import CountrySerializer
from bluebottle.members.serializers import UserProfileSerializer, UserPreviewSerializer
from bluebottle.organizations.serializers import OrganizationPreviewSerializer
from bluebottle.projects.models import ProjectBudgetLine, ProjectDocument, Project
from bluebottle.tasks.models import Task, TaskMember, Skill
from bluebottle.utils.serializers import MoneySerializer
from bluebottle.utils.fields import SafeField
from bluebottle.wallposts.models import MediaWallpostPhoto, MediaWallpost, TextWallpost
from bluebottle.votes.models import Vote


class ProjectPhaseLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase


class ProjectPhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase


class ProjectThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectTheme
        fields = ('id', 'name', 'description')


class ProjectCountrySerializer(CountrySerializer):
    subregion = serializers.CharField(source='subregion.name')

    class Meta:
        model = Country
        fields = ('id', 'name', 'subregion', 'code')


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


class ProjectDocumentSerializer(serializers.ModelSerializer):
    file = PrivateFileSerializer(url_name='project-document-file')
    project = serializers.SlugRelatedField(slug_field='slug', queryset=Project.objects)

    class Meta:
        model = ProjectDocument
        fields = ('id', 'project', 'file')


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    amount_asked = MoneySerializer()
    amount_donated = MoneySerializer()
    amount_extra = MoneySerializer()
    amount_needed = MoneySerializer()
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
    story = SafeField()
    supporter_count = serializers.IntegerField()
    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')
    vote_count = serializers.IntegerField()

    def __init__(self, *args, **kwargs):
        super(ProjectSerializer, self).__init__(*args, **kwargs)

    def get_has_voted(self, obj):
        return Vote.has_voted(self.context['request'].user, obj)

    class Meta:
        model = Project
        fields = ('id',
                  'allow_overfunding',
                  'amount_asked',
                  'amount_donated',
                  'amount_extra',
                  'amount_needed',
                  'budget_lines',
                  'categories',
                  'celebrate_results',
                  'country',
                  'created',
                  'currencies',
                  'deadline',
                  'description',
                  'full_task_count',
                  'has_voted',
                  'image',
                  'is_funding',
                  'language',
                  'latitude',
                  'location',
                  'longitude',
                  'open_task_count',
                  'organization',
                  'owner',
                  'people_needed',
                  'people_registered',
                  'pitch',
                  'project_type',
                  'realized_task_count',
                  'status',
                  'status',
                  'story',
                  'supporter_count',
                  'task_count',
                  'theme',
                  'title',
                  'video_html',
                  'video_url',
                  'vote_count',
                  'voting_deadline',)


class PermissionField(serializers.Field):
    def __init__(self, permission_class, *args, **kwargs):
        self.permissions = permission_class
        kwargs['read_only'] = True

        super(PermissionField, self).__init__(*args, **kwargs)

    def get_attribute(self, obj):
        return obj

    def to_representation(self, value):
        import ipdb;ipdb.set_trace()
        self.permissions().get_permissions(self.context['request'])


class ProjectPreviewSerializer(ProjectSerializer):
    categories = serializers.SlugRelatedField(many=True, read_only=True, slug_field='slug')
    image = ImageSerializer(required=False)
    owner = UserPreviewSerializer()
    skills = serializers.SerializerMethodField()
    theme = ProjectThemeSerializer()
    permissions = PermissionField(ProjectPermissions)

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
                  'categories',
                  'celebrate_results',
                  'country',
                  'deadline',
                  'full_task_count',
                  'image',
                  'is_campaign',
                  'is_funding',
                  'latitude',
                  'location',
                  'longitude',
                  'open_task_count',
                  'owner',
                  'people_needed',
                  'people_registered',
                  'pitch',
                  'project_type',
                  'realized_task_count',
                  'skills',
                  'status',
                  'task_count',
                  'theme',
                  'title',
                  'vote_count',
                  'voting_deadline',)


class ProjectTinyPreviewSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    image = SorlImageField('400x300', crop='center')

    class Meta:
        model = Project
        fields = ('id', 'title', 'slug', 'status', 'image', 'latitude', 'longitude')


class ManageTaskSerializer(serializers.ModelSerializer):
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects)
    time_needed = serializers.DecimalField(min_value=0.0, max_digits=5, decimal_places=2)

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
                  'type',)


class ManageProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)

    account_bic = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    account_details = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    amount_asked = MoneySerializer(required=False, allow_null=True)
    amount_donated = MoneySerializer(read_only=True)
    amount_needed = MoneySerializer(read_only=True)
    budget_lines = ProjectBudgetLineSerializer(many=True, source='projectbudgetline_set', read_only=True)
    currencies = serializers.JSONField(read_only=True)
    documents = ProjectDocumentSerializer(many=True, read_only=True)
    editable = serializers.BooleanField(read_only=True)
    image = ImageSerializer(required=False, allow_null=True)
    is_funding = serializers.ReadOnlyField()
    location = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=Location.objects)
    people_needed = serializers.IntegerField(read_only=True)
    people_registered = serializers.IntegerField(read_only=True)
    pitch = serializers.CharField(required=False, allow_null=True)
    slug = serializers.CharField(read_only=True)
    status = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=ProjectPhase.objects)
    story = SafeField(required=False, allow_blank=True)
    tasks = ManageTaskSerializer(many=True, source='task_set', read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name='project_manage_detail', lookup_field='slug')
    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')
    viewable = serializers.BooleanField(read_only=True)

    @staticmethod
    def validate_account_number(value):

        if value:
            country_code = value[:2]
            digits_regex = re.compile('\d{2}')
            check_digits = value[2:4]

            # Only try iban validaton when the field matches start of
            # iban format as the field can also contain non-iban
            # account numbers.
            # Expecting something like: NL18xxxxxxxxxx
            iban_validator = IBANValidator()
            if country_code in iban_validator.validation_countries.keys() and \
                    digits_regex.match(check_digits):
                iban_validator(value)
        return value

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

    class Meta:
        model = Project
        fields = ('id',
                  'account_bank_country',
                  'account_details',
                  'account_bic',
                  'account_holder_address',
                  'account_holder_city',
                  'account_holder_country',
                  'account_holder_name',
                  'account_holder_postal_code',
                  'account_number',
                  'amount_asked',
                  'amount_donated',
                  'amount_needed',
                  'budget_lines',
                  'categories',
                  'country',
                  'created',
                  'currencies',
                  'deadline',
                  'description',
                  'documents',
                  'editable',
                  'image',
                  'is_funding',
                  'language',
                  'latitude',
                  'location',
                  'longitude',
                  'organization',
                  'people_needed',
                  'people_registered',
                  'pitch',
                  'place',
                  'project_type',
                  'slug',
                  'status',
                  'story',
                  'tasks',
                  'theme',
                  'title',
                  'url',
                  'video_html',
                  'video_url',
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
