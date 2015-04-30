from django.utils.translation import ugettext as _

from django_iban.validators import iban_validator, swift_bic_validator
from rest_framework import serializers
from bs4 import BeautifulSoup

from bluebottle.bb_accounts.serializers import UserPreviewSerializer
from bluebottle.bluebottle_drf2.serializers import (
    SorlImageField, ImageSerializer, TaggableSerializerMixin, TagSerializer, PrivateFileSerializer)
from bluebottle.geo.models import Country

from bluebottle.utils.model_dispatcher import (get_project_model,
                                               get_project_phaselog_model,
                                               get_project_document_model)
from bluebottle.utils.serializer_dispatcher import get_serializer_class
from bluebottle.utils.serializers import MetaField
from bluebottle.bb_projects.models import ProjectTheme, ProjectPhase
from bluebottle.geo.serializers import CountrySerializer

PROJECT_MODEL = get_project_model()
PROJECT_PHASELOG_MODEL = get_project_phaselog_model()

PROJECT_DOCUMENT_MODEL = get_project_document_model()


class StoryField(serializers.WritableField):

    def to_native(self, value):
        """ Reading / Loading the story field """
        return value

    def from_native(self, data):
        """ Saving the story text """
        # Convert &gt; and &lt; back to HTML tags so Beautiful
        # Soup can clean unwanted tags.
        # Script tags are sent by redactor as "&lt;;script&gt;;",
        # Iframe tags have just one semicolon.
        data = data.replace("&lt;;", "<").replace(
            "&gt;;", ">").replace("&lt;", "<").replace("&gt;", ">")
        soup = BeautifulSoup(data, "html.parser")
        [s.extract() for s in soup(['script', 'iframe'])]
        return str(soup)


class ProjectPhaseLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = PROJECT_PHASELOG_MODEL


class ProjectPhaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectPhase


class ProjectCountrySerializer(serializers.ModelSerializer):
    subregion = serializers.CharField(source='subregion.name')

    class Meta:
        model = Country
        fields = ('id', 'name', 'subregion')


class ProjectThemeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectTheme
        fields = ('id', 'name')


class ProjectDocumentSerializer(serializers.ModelSerializer):
    file = PrivateFileSerializer()

    class Meta:
        model = PROJECT_DOCUMENT_MODEL
        fields = ('id', 'project', 'file')


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    owner = UserPreviewSerializer()
    image = ImageSerializer(required=False)
    country = CountrySerializer()
    tags = TagSerializer()

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
                  'amount_needed', 'amount_extra'
                  )


class ProjectPreviewSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    image = SorlImageField('image', '400x300', crop='center')
    country = ProjectCountrySerializer(source='country')
    pitch = serializers.CharField(source='pitch')
    theme = ProjectThemeSerializer(source='theme')
    owner = UserPreviewSerializer()

    class Meta:
        model = PROJECT_MODEL
        fields = ('id', 'title', 'status', 'image', 'country', 'pitch',
                  'theme', 'owner', 'amount_asked', 'amount_donated',
                  'amount_needed', 'amount_extra',
                  'deadline', 'latitude', 'longitude')


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

    tasks = get_serializer_class('TASKS_TASK_MODEL')(many=True, source='task_set', read_only=True)
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
                  'account_number', 'account_bic',
                  'account_bank_country', 'tasks')
