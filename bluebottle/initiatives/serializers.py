from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework_json_api.serializers import ModelSerializer
from rest_framework_json_api.relations import (
    ResourceRelatedField, PolymorphicResourceRelatedField
)

from bluebottle.bb_projects.models import ProjectTheme
from bluebottle.bluebottle_drf2.serializers import (
    OEmbedField, ImageSerializer as OldImageSerializer, SorlImageField
)
from bluebottle.utils.fields import SafeField, ValidationErrorsField, RequiredErrorsField
from bluebottle.activities.serializers import ActivitySerializer
from bluebottle.categories.models import Category
from bluebottle.geo.models import Geolocation, Location
from bluebottle.organizations.models import Organization, OrganizationContact
from bluebottle.files.models import Image
from bluebottle.files.serializers import ImageSerializer, ImageField
from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings
from bluebottle.members.models import Member
from bluebottle.transitions.serializers import (
    AvailableTransitionsField, TransitionSerializer
)
from bluebottle.utils.serializers import (
    ResourcePermissionField, NoCommitMixin
)


class ThemeSerializer(ModelSerializer):

    class Meta:
        model = ProjectTheme
        fields = ('id', 'slug', 'name', 'description')

    class JSONAPIMeta:
        resource_name = 'themes'


class CategorySerializer(ModelSerializer):
    image = OldImageSerializer(required=False)
    image_logo = OldImageSerializer(required=False)
    slug = serializers.CharField(read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'title', 'slug', 'description', 'image', 'image_logo')

    class JSONAPIMeta:
        resource_name = 'categories'


class MemberSerializer(ModelSerializer):
    avatar = SorlImageField('133x133', source='picture', crop='center')
    full_name = serializers.ReadOnlyField(source='get_full_name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    short_name = serializers.ReadOnlyField(source='get_short_name', read_only=True)

    class Meta:
        model = Member
        fields = (
            'id', 'first_name', 'last_name', 'initials', 'avatar',
            'full_name', 'short_name', 'is_active', 'date_joined'
        )

    class JSONAPIMeta:
        resource_name = 'members'


class InitiativeImageSerializer(ImageSerializer):
    sizes = {
        'preview': '200x300',
        'large': '400x500'
    }
    content_view_name = 'initiative-image'
    relationship = 'initiative_set'


class InitiativeSerializer(NoCommitMixin, ModelSerializer):
    image = ImageField(required=False, allow_null=True)
    owner = ResourceRelatedField(read_only=True)
    permissions = ResourcePermissionField('initiative-detail', view_args=('pk',))
    reviewer = ResourceRelatedField(read_only=True)
    activity_manager = ResourceRelatedField(read_only=True)
    activities = PolymorphicResourceRelatedField(
        ActivitySerializer, many=True, read_only=True
    )
    slug = serializers.CharField(read_only=True)
    story = SafeField(required=False, allow_blank=True, allow_null=True)
    title = serializers.CharField(allow_blank=True)
    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')

    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    transitions = AvailableTransitionsField()

    included_serializers = {
        'categories': 'bluebottle.initiatives.serializers.CategorySerializer',
        'image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'reviewer': 'bluebottle.initiatives.serializers.MemberSerializer',
        'promoter': 'bluebottle.initiatives.serializers.MemberSerializer',
        'activity_manager': 'bluebottle.initiatives.serializers.MemberSerializer',
        'place': 'bluebottle.geo.serializers.GeolocationSerializer',
        'location': 'bluebottle.geo.serializers.LocationSerializer',
        'theme': 'bluebottle.initiatives.serializers.ThemeSerializer',
        'organization': 'bluebottle.organizations.serializers.OrganizationSerializer',
        'organization_contact': 'bluebottle.organizations.serializers.OrganizationContactSerializer',
        'activities': 'bluebottle.activities.serializers.ActivitySerializer',
        'activities.location': 'bluebottle.geo.serializers.GeolocationSerializer',
    }

    class Meta:
        model = Initiative
        fsm_fields = ['status']
        fields = (
            'id', 'title', 'pitch', 'categories',
            'owner', 'reviewer', 'promoter', 'activity_manager',
            'slug', 'has_organization', 'organization',
            'organization_contact', 'story', 'video_html', 'image',
            'theme', 'place', 'location', 'activities',
            'errors', 'required',
        )

        meta_fields = ('permissions', 'transitions', 'status', 'created', 'required', 'errors', )

    class JSONAPIMeta:
        included_resources = [
            'owner', 'reviewer', 'promoter', 'activity_manager',
            'categories', 'theme', 'place', 'location',
            'image', 'organization', 'organization_contact', 'activities', 'activities.location',
        ]
        resource_name = 'initiatives'


def _error_messages_for(label):
    return {
        'error_messages': {'required': "'{}' is required".format(label)}
    }


class OrganizationSubmitSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, error_messages={'blank': _('Name is required')})

    def __init__(self, *args, **kwargs):
        super(OrganizationSubmitSerializer, self).__init__(*args, **kwargs)

    def validate_empty_values(self, data):
        if self.parent.initial_data['has_organization'] and not data:
            return (False, data)
        else:
            return (False if data else True, data)

    class Meta:
        model = Organization
        fields = ('name', )


class OrganizationContactSubmitSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, error_messages={'blank': _('Name is required')})
    email = serializers.CharField(required=True, error_messages={'blank': _('Email is required')})

    def validate_empty_values(self, data):
        if self.parent.initial_data['has_organization'] and not data:
            return (False, data)
        else:
            return (False if data else True, data)

    class Meta:
        model = OrganizationContact
        fields = ('name', 'email', 'phone', )


class InitiativeSubmitSerializer(ModelSerializer):
    title = serializers.CharField(
        required=True,
        error_messages={'blank': _('Title is required')}
    )
    pitch = serializers.CharField(required=True, error_messages={'blank': _('Pitch is required')})
    story = serializers.CharField(required=True, error_messages={'blank': _('Story is required')})

    theme = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=ProjectTheme.objects.all(),
        error_messages={'null': _('Theme is required')}
    )
    image = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Image.objects.all(),
        error_messages={'null': _('Image is required')}
    )
    owner = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Member.objects.all(),
        error_messages={'null': _('Owner is required')}
    )
    place = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        allow_empty=True,
        queryset=Geolocation.objects.all()
    )
    organization = OrganizationSubmitSerializer(
        error_messages={'null': _('Organization is required')}
    )
    organization_contact = OrganizationContactSubmitSerializer(
        error_messages={'null': _('Organization contact is required')}
    )

    # TODO add dependent fields: has_organization/organization/organization_contact and
    # place / location

    def validate(self, data):
        """
        Check that location or place is set
        """
        if Location.objects.count():
            if not self.initial_data['location']:
                raise serializers.ValidationError("Location is required")
        elif not self.initial_data['place']:
            raise serializers.ValidationError("Place is required")
        return data

    class Meta:
        model = Initiative
        fields = (
            'title', 'pitch', 'owner',
            'has_organization', 'organization',
            'organization_contact', 'story', 'video_url', 'image',
            'theme', 'place',
        )


class InitiativeReviewTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Initiative.objects.all())
    field = 'transitions'
    included_serializers = {
        'resource': 'bluebottle.initiatives.serializers.InitiativeSerializer',
    }

    class JSONAPIMeta:
        included_resources = ['resource']
        resource_name = 'initiative-transitions'


class InitiativePlatformSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InitiativePlatformSettings

        fields = (
            'activity_types',
            'require_organization',
        )
