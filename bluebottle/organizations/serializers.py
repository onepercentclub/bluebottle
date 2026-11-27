from builtins import object

from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.utils import get_stats_for_activities
from bluebottle.bluebottle_drf2.serializers import (
    ImageSerializer,
    SorlImageField,
)
from bluebottle.organizations.models import Organization, OrganizationContact, OrganizationMember
from bluebottle.utils.fields import (
    RichTextField,
    ValidationErrorsField,
    RequiredErrorsField,
)
from bluebottle.utils.serializers import NoCommitMixin, ResourcePermissionField


class OrganizationPreviewSerializer(ModelSerializer):
    image = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    activity_count = serializers.SerializerMethodField()
    slogan = serializers.ReadOnlyField()
    story = serializers.ReadOnlyField()

    name = serializers.ReadOnlyField()
    website = serializers.ReadOnlyField()

    created = serializers.ReadOnlyField()

    def get_activity_count(self, obj):
        return {
            'succeeded': obj.succeeded_activities_count,
            'open': obj.open_activities_count
        }

    class Meta:
        model = Organization
        fields = (
            "id",
            "slug",
            "name",
            "image",
            "logo",
            "slogan",
            "story",
            "website",
            "verified",
            "activity_count",
        )
        meta_fields = (
            "created",
        )

    def _get_file(self, obj, field_name):
        # Elasticsearch only stores the file name; rebuild a FieldFile so we
        # can reuse the regular image fields to generate the thumbnail urls.
        value = getattr(obj, field_name, None)
        name = getattr(value, 'file', None) if value else None
        if not name:
            return None

        field = Organization._meta.get_field(field_name)
        return field.attr_class(None, field, name)

    def get_image(self, obj):
        file = self._get_file(obj, 'image')
        if file:
            return SorlImageField('465x262', crop='center').to_representation(file) or None

    def get_logo(self, obj):
        file = self._get_file(obj, 'logo')
        if file:
            field = ImageSerializer()
            field.bind('logo', self)
            return field.to_representation(file)

    class JSONAPIMeta:
        resource_name = "organizations/preview"


class OrganizationSerializer(NoCommitMixin, ModelSerializer):
    description = serializers.CharField(
        source='slogan', required=False, allow_blank=True, allow_null=True
    )
    slogan = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    story = RichTextField(required=False, allow_blank=True, allow_null=True)
    slug = serializers.SlugField(allow_null=True, required=False)
    name = serializers.CharField(required=True)
    website = serializers.CharField(allow_blank=True, required=False)
    logo = ImageSerializer(required=False, allow_null=True)
    cover_image = SorlImageField(
        '465x262', crop='center', source='image', read_only=True
    )
    color = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    background_color = serializers.CharField(read_only=True)
    text_color = serializers.CharField(read_only=True)

    permissions = ResourcePermissionField('organization_detail', view_args=('pk',))

    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

    class Meta(object):
        model = Organization
        fields = (
            'id', 'name', 'slug', 'description', 'slogan', 'story',
            'website', 'owner', 'logo', 'cover_image',
            'color', 'background_color', 'text_color',
            'required', 'errors', 'verified',
        )

        meta_fields = ['created', 'updated', 'errors', 'required', 'permissions']

    class JSONAPIMeta(object):
        resource_name = 'organizations'
        included_resources = ['owner', ]


class OrganizationMemberSerializer(ModelSerializer):
    included_serializers = {
        'member': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta(object):
        model = OrganizationMember
        fields = ('id', 'member', 'role', 'created')

    class JSONAPIMeta(object):
        resource_name = 'organization-members'
        included_resources = ['member']


class OrganizationDetailSerializer(OrganizationSerializer):
    cover_image = SorlImageField(
        '1280x720', crop='center', source='image', read_only=True
    )
    stats = serializers.SerializerMethodField()
    members = ResourceRelatedField(many=True, read_only=True)

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'members': 'bluebottle.organizations.serializers.OrganizationMemberSerializer',
    }

    def get_stats(self, obj):
        return get_stats_for_activities(obj.activities.all())

    def get_fields(self):
        fields = super().get_fields()

        user = self.context['request'].user
        if not (
            user.is_staff or
            user.is_superuser or
            (
                self.instance and
                user.is_authenticated and
                self.instance.members.filter(member=user).exists()
            )
        ):
            del fields['members']
        return fields

    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + ('stats', 'members')
        meta_fields = OrganizationSerializer.Meta.meta_fields + ['stats']

    class JSONAPIMeta(OrganizationSerializer.JSONAPIMeta):
        included_resources = ['owner', 'members', 'members.member']


class OrganizationContactSerializer(NoCommitMixin, ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    email = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

    class Meta(object):
        model = OrganizationContact
        fields = (
            'id', 'name', 'email', 'phone',
            'required', 'errors',
        )

        meta_fields = ['created', 'updated', 'errors', 'required']

    class JSONAPIMeta(object):
        resource_name = 'organization-contacts'
        included_resources = ['owner', ]
