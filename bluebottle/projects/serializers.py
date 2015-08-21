from django.utils.translation import ugettext as _

from django_iban.validators import iban_validator, swift_bic_validator
from rest_framework import serializers
from bs4 import BeautifulSoup

from bluebottle.projects.models import ProjectBudgetLine
from bluebottle.bluebottle_drf2.serializers import (
    EuroField, OEmbedField, SorlImageField, ImageSerializer,
    TaggableSerializerMixin, TagSerializer, PrivateFileSerializer)
from bluebottle.donations.models import Donation
from bluebottle.geo.models import Country
from bluebottle.geo.serializers import CountrySerializer
from bluebottle.utils.model_dispatcher import (get_project_model,
                                               get_project_phaselog_model,
                                               get_project_document_model)
from bluebottle.utils.serializer_dispatcher import get_serializer_class
from bluebottle.utils.serializers import MetaField
from bluebottle.bb_projects.models import ProjectTheme, ProjectPhase

PROJECT_MODEL = get_project_model()
PROJECT_DOCUMENT_MODEL = get_project_document_model()
PROJECT_PHASELOG_MODEL = get_project_phaselog_model()


class ProjectPhaseLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PROJECT_PHASELOG_MODEL


class ProjectPhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase


class ProjectThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectTheme
        fields = ('id', 'name')


class StoryField(serializers.WritableField):
    def to_native(self, value):
        """ Reading / Loading the story field """
        return value

    def from_native(self, data):
        """
        Saving the story text

        Convert &gt; and &lt; back to HTML tags so Beautiful Soup can clean
        unwanted tags. Script tags are sent by redactor as
        "&lt;;script&gt;;", Iframe tags have just one semicolon.
        """
        data = data.replace("&lt;;", "<").replace("&gt;;", ">")
        data = data.replace("&lt;", "<").replace("&gt;", ">")
        soup = BeautifulSoup(data, "html.parser")
        [s.extract() for s in soup(['script', 'iframe'])]
        return str(soup)


class ProjectCountrySerializer(CountrySerializer):
    subregion = serializers.CharField(source='subregion.name')

    class Meta:
        model = Country
        fields = ('id', 'name', 'subregion', 'code')


class ProjectBudgetLineSerializer(serializers.ModelSerializer):
    amount = EuroField()
    project = serializers.SlugRelatedField(slug_field='slug')

    class Meta:
        model = ProjectBudgetLine
        fields = ('id', 'project', 'description', 'amount')


class BasicProjectBudgetLineSerializer(serializers.ModelSerializer):
    amount = EuroField()

    class Meta:
        model = ProjectBudgetLine
        fields = ('description', 'amount')


class ProjectDocumentSerializer(serializers.ModelSerializer):
    file = PrivateFileSerializer()
    project = serializers.SlugRelatedField(slug_field='slug')

    class Meta:
        model = PROJECT_DOCUMENT_MODEL
        fields = ('id', 'project', 'file')


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    owner = get_serializer_class('AUTH_USER_MODEL', 'preview')()
    image = ImageSerializer(required=False)
    tags = TagSerializer()
    task_count = serializers.IntegerField(source='task_count')
    country = ProjectCountrySerializer(source='country')
    story = StoryField()
    is_funding = serializers.Field()
    budget_lines = BasicProjectBudgetLineSerializer(
        many=True, source='projectbudgetline_set', read_only=True)
    video_html = OEmbedField(source='video_url', maxwidth='560',
                             maxheight='315')
    partner = serializers.SlugRelatedField(slug_field='slug',
                                           source='partner_organization')
    location = serializers.PrimaryKeyRelatedField(required=False)
    vote_count = serializers.IntegerField(source='vote_count')

    meta_data = MetaField(
        title='get_meta_title',
        fb_title='get_fb_title',
        description='pitch',
        keywords='tags',
        image_source='image',
        tweet='get_tweet',
    )

    def __init__(self, *args, **kwargs):
        super(ProjectSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = PROJECT_MODEL
        fields = ('id', 'created', 'title', 'pitch', 'organization',
                  'description', 'owner', 'status', 'meta_data', 'image',
                  'country', 'theme', 'tags', 'meta_data', 'language',
                  'latitude', 'longitude', 'amount_asked', 'amount_donated',
                  'amount_needed', 'amount_extra', 'allow_overfunding',
                  'task_count', 'amount_asked', 'amount_donated',
                  'amount_needed', 'amount_extra', 'story', 'budget_lines',
                  'status', 'deadline', 'is_funding', 'vote_count',
                  'voting_deadline', 'latitude', 'longitude', 'video_url',
                  'video_html', 'partner', 'location')


class ProjectPreviewSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    image = SorlImageField('image', '400x300', crop='center')
    country = ProjectCountrySerializer(source='country')
    pitch = serializers.CharField(source='pitch')
    theme = ProjectThemeSerializer(source='theme')
    owner = get_serializer_class('AUTH_USER_MODEL', 'preview')()
    task_count = serializers.IntegerField(source='task_count')
    partner = serializers.SlugRelatedField(slug_field='slug',
                                           source='partner_organization')
    is_funding = serializers.Field()
    people_requested = serializers.Field()
    people_registered = serializers.Field()
    location = serializers.PrimaryKeyRelatedField(required=False)
    vote_count = serializers.IntegerField(source='vote_count')

    class Meta:
        model = PROJECT_MODEL
        fields = ('id', 'title', 'status', 'image', 'country', 'pitch',
                  'theme', 'owner', 'amount_asked', 'amount_donated',
                  'amount_needed', 'amount_extra', 'deadline', 'latitude',
                  'longitude', 'task_count', 'allow_overfunding', 'is_campaign',
                  'partner', 'is_funding', 'people_requested',
                  'people_registered', 'location', 'vote_count',
                  'voting_deadline')


class ManageProjectSerializer(TaggableSerializerMixin,
                              serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)

    url = serializers.HyperlinkedIdentityField(
        view_name='project_manage_detail')
    editable = serializers.BooleanField(read_only=True)
    viewable = serializers.BooleanField(read_only=True)
    status = serializers.PrimaryKeyRelatedField(required=False)
    location = serializers.PrimaryKeyRelatedField(required=False)
    image = ImageSerializer(required=False)
    pitch = serializers.CharField(required=False)
    slug = serializers.CharField(read_only=True)
    tags = TagSerializer()
    amount_asked = serializers.CharField(required=False)
    amount_donated = serializers.CharField(read_only=True)
    amount_needed = serializers.CharField(read_only=True)
    budget_lines = ProjectBudgetLineSerializer(many=True,
                                               source='projectbudgetline_set',
                                               read_only=True)
    video_html = OEmbedField(source='video_url', maxwidth='560',
                             maxheight='315')
    story = StoryField(required=False)
    partner = serializers.SlugRelatedField(slug_field='slug',
                                           source='partner_organization',
                                           required=False)
    is_funding = serializers.Field()

    tasks = get_serializer_class('TASKS_TASK_MODEL')(many=True,
                                                     source='task_set',
                                                     read_only=True)
    documents = ProjectDocumentSerializer(
        many=True, source='documents', read_only=True)

    def validate_account_iban(self, attrs, source):
        value = attrs.get(source)
        if value:
            iban_validator(value)
        return attrs

    def validate_account_bic(self, attrs, source):
        value = attrs.get(source)
        if value:
            swift_bic_validator(value)
        return attrs

    def validate_status(self, attrs, source):
        value = attrs.get(source, None)
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
                current_status = PROJECT_MODEL.objects.get(
                    slug=self.data['slug']).status
            except KeyError:
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
                if (not (proposed_status == current_status) and
                        not (proposed_status and
                                 (current_status == new_status or
                                          current_status == needs_work_status) and
                                     proposed_status == submit_status)):
                    raise serializers.ValidationError(
                        _("You can not change the project state."))

        attrs[source] = value
        return attrs

    class Meta:
        model = PROJECT_MODEL
        fields = ('id', 'title', 'description', 'editable', 'viewable',
                  'status', 'image', 'pitch', 'slug', 'tags', 'created',
                  'url', 'country', 'location', 'place', 'theme',
                  'organization', 'language', 'account_holder_name',
                  'account_holder_address', 'account_holder_postal_code',
                  'account_holder_city', 'account_holder_country',
                  'account_number', 'account_bic', 'documents',
                  'account_bank_country', 'tasks', 'amount_asked',
                  'amount_donated', 'amount_needed', 'video_url',
                  'video_html', 'partner', 'is_funding', 'story',
                  'budget_lines', 'deadline', 'latitude', 'longitude')


class ProjectSupporterSerializer(serializers.ModelSerializer):
    """
    For displaying donations on project and member pages.
    """
    member = get_serializer_class('AUTH_USER_MODEL', 'preview')(source='user')
    project = ProjectPreviewSerializer()
    date_donated = serializers.DateTimeField(source='ready')

    class Meta:
        model = Donation
        fields = ('date_donated', 'project', 'member',)


class ProjectDonationSerializer(serializers.ModelSerializer):
    member = get_serializer_class('AUTH_USER_MODEL', 'preview')(source='user')
    date_donated = serializers.DateTimeField(source='ready')
    amount = EuroField(source='amount')

    class Meta:
        model = Donation
        fields = ('member', 'date_donated', 'amount',)
