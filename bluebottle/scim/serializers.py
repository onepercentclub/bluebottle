from builtins import object
from django.contrib.auth.models import Group
from django.urls import reverse

from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers, validators

from bluebottle.segments.models import Segment
from bluebottle.scim.models import SCIMPlatformSettings
from bluebottle.scim.utils import SCIMPath

from bluebottle.members.models import Member
from bluebottle.geo.models import Location


class NonNestedSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        kwargs['source'] = '*'
        super(NonNestedSerializer, self).__init__(*args, **kwargs)


class NameSerializer(NonNestedSerializer):

    givenName = serializers.CharField(source='first_name')
    familyName = serializers.CharField(source='last_name')


class EmailsField(serializers.CharField):
    default_error_messages = {
        'invalid': _('Not a valid email value.'),
        'blank': _('This field may not be blank.'),
        'max_length': _('Ensure this field has no more than {max_length} characters.'),
        'min_length': _('Ensure this field has at least {min_length} characters.')
    }

    def to_representation(self, value):
        value = super(EmailsField, self).to_representation(value)
        return [{
            'primary': True,
            'type': 'work',
            'value': value

        }]

    def to_internal_value(self, value):
        return super(EmailsField, self).to_internal_value(value[0]['value'])

    def run_validation(self, data=None):
        if not isinstance(data, list) or not isinstance(data[0], dict) or 'value' not in data[0]:
            self.fail('invalid')

        if not data[0].get('value'):
            self.fail('blank')

        return super(EmailsField, self).run_validation(data)


class AddressesField(serializers.RelatedField):
    queryset = Location.objects.all()
    initial = []

    def get_attribute(self, instance):
        value = getattr(instance, self.source)
        if value is None:
            return False

        return value

    def to_representation(self, value):
        if not value:
            return []

        return [{
            'type': 'work',
            'locality': value.name

        }]

    def to_internal_value(self, value):
        if value and 'locality' in value[0]:
            queryset = self.get_queryset()
            location_name = value[0]['locality']
            try:
                return queryset.get(slug=slugify(location_name))
            except Location.DoesNotExist:
                return queryset.create(name=location_name)
            except (TypeError, ValueError):
                self.fail('invalid')


class SchemaSerializer(NonNestedSerializer):
    def to_representation(self, obj):
        return self.parent.resource_schemas

    def to_internal_value(self, value):
        return {}


class LocationField(serializers.CharField):
    def to_representation(self, obj):
        return reverse(self.parent.parent.detail_view_name, args=(obj, ))


class SCIMIdField(serializers.CharField):
    def __init__(self, type, *args, **kwargs):
        self.type = type
        super(SCIMIdField, self).__init__(*args, **kwargs)

    def to_internal_value(self, value):
        value = super(SCIMIdField, self).to_internal_value(value)
        return value.replace('goodup-{}-'.format(self.type), '')

    def to_representation(self, id):
        result = super(SCIMIdField, self).to_representation(id)

        return 'goodup-{}-{}'.format(self.type, result)


class MetaSerializer(NonNestedSerializer):
    location = LocationField(source='id', read_only=True)

    def to_representation(self, obj):
        representation = super(MetaSerializer, self).to_representation(obj)
        representation['resourceType'] = self.parent.resource_type
        return representation


class UserGroupSerializer(serializers.ModelSerializer):
    id = SCIMIdField('group')

    class Meta(object):
        model = Group
        fields = ('id', 'name',)


class SCIMMemberSerializer(serializers.ModelSerializer):
    id = SCIMIdField('user', read_only=True)
    resource_schemas = ["urn:ietf:params:scim:schemas:core:2.0:User"]
    resource_type = 'User'
    detail_view_name = 'scim-user-detail'

    userName = serializers.CharField(
        source='remote_id', required=False,
        validators=[
            validators.UniqueValidator(
                queryset=Member.objects.filter(scim_external_id__isnull=False)
            )
        ]
    )
    externalId = serializers.CharField(source='scim_external_id')

    name = NameSerializer()
    emails = EmailsField(
        source='email',
        allow_blank=False,
        validators=[
            validators.UniqueValidator(
                queryset=Member.objects.filter(scim_external_id__isnull=False), lookup='iexact'
            )
        ]
    )
    addresses = AddressesField(
        source='location', required=False
    )

    active = serializers.BooleanField(source='is_active')
    groups = serializers.SerializerMethodField(read_only=True)
    schemas = SchemaSerializer(read_only=False)
    meta = MetaSerializer(required=False)

    def create(self, validated_data):
        validated_data['welcome_email_is_sent'] = True
        instance = super(SCIMMemberSerializer, self).create(validated_data)

        return instance

    def get_groups(self, obj):
        return UserGroupSerializer(
            obj.groups.exclude(
                name='Authenticated'
            ),
            many=True,
            read_only=True
        ).data

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)

        segment_settings = SCIMPlatformSettings.objects.get().segments

        for path, segment_type in segment_settings:
            segment_name = path.get(self.initial_data)
            if segment_name:
                (segment, _created) = Segment.objects.get_or_create(
                    segment_type=segment_type,
                    slug=slugify(segment_name),
                    defaults={
                        'name': segment_name
                    }
                )

                self.instance.segments.remove(*self.instance.segments.filter(segment_type=segment_type))
                self.instance.segments.add(segment)

        return result

    def to_representation(self, obj):
        data = super().to_representation(obj)

        segment_settings = SCIMPlatformSettings.objects.get().segments

        for path, segment_type in segment_settings:
            try:
                segment = obj.segments.get(segment_type=segment_type)
                path.set(data, segment.name)
            except Segment.DoesNotExist:
                pass

        return data

    class Meta(object):
        model = Member
        fields = (
            'id', 'externalId', 'userName', 'name', 'emails', 'active', 'groups', 'schemas', 'meta',
            'addresses',
        )


class GroupMemberListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        return super(GroupMemberListSerializer, self).to_representation(
            data.filter(
                is_superuser=False, is_anonymized=False
            ).exclude(email='devteam+accounting@onepercentclub.com')
        )


class GroupMemberSerializer(serializers.ModelSerializer):
    value = SCIMIdField('user', source='pk')
    ref = serializers.SerializerMethodField(method_name='get_ref')
    type = serializers.SerializerMethodField()

    def get_ref(self, obj):
        return reverse('scim-user-detail', args=(obj.pk, ))

    def get_type(self, obj):
        return 'User'

    def get_fields(self):
        result = super(GroupMemberSerializer, self).get_fields()

        result['$ref'] = result.pop('ref')
        return result

    class Meta(object):
        model = Member
        list_serializer_class = GroupMemberListSerializer
        fields = ('value', 'ref', 'type')


class SCIMGroupSerializer(serializers.ModelSerializer):
    resource_schemas = ["urn:ietf:params:scim:schemas:core:2.0:Group"]
    resource_type = 'Group'
    detail_view_name = 'scim-group-detail'

    id = SCIMIdField('group', read_only=True)
    displayName = serializers.CharField(source='name', read_only=True)
    members = GroupMemberSerializer(many=True, source='user_set', read_only=False)
    schemas = SchemaSerializer(read_only=False, required=False)
    meta = MetaSerializer(required=False)

    class Meta(object):
        model = Group
        fields = ('id', 'displayName', 'schemas', 'meta', 'members', )

    def update(self, obj, data):
        members = data.pop('user_set')
        obj.user_set.clear()
        for member in members:
            try:
                user = Member.objects.get(pk=member['pk'])
                obj.user_set.add(user)
                if obj.name == 'Staff':
                    user.is_staff = True
                    user.save()
            except Member.DoesNotExist:
                pass
            except ValueError:
                pass

        return super(SCIMGroupSerializer, self).update(obj, data)


class SCIMPatchSerializer(serializers.Serializer):
    schemas = serializers.ListField()
    Operations = serializers.ListField()

    class Meta:
        fields = ('schemas', 'Operations')

    def patch(self, data):
        if self.is_valid():
            for operation in self.validated_data['Operations']:
                path = SCIMPath(operation['path'])
                value = operation['value']

                path.set(data, value)

        return data
