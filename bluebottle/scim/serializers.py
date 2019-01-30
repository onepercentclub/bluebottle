from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse

from rest_framework import serializers, validators

from bluebottle.members.models import Member


class NonNestedSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        kwargs['source'] = '*'
        super(NonNestedSerializer, self).__init__(*args, **kwargs)


class NameSerializer(NonNestedSerializer):

    givenName = serializers.CharField(source='first_name')
    familyName = serializers.CharField(source='last_name')


class EmailsField(serializers.CharField):
    def to_representation(self, value):
        value = super(EmailsField, self).to_representation(value)
        return [{
            'primary': True,
            'type': 'work',
            'value': value

        }]

    def to_internal_value(self, value):
        return super(EmailsField, self).to_internal_value(value[0]['value'])


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name',)


class SchemaSerializer(NonNestedSerializer):
    def to_representation(self, obj):
        return self.parent.resource_schemas

    def to_internal_value(self, value):
        return {}


class LocationField(serializers.CharField):
    def to_representation(self, obj):
        return reverse(self.parent.parent.detail_view_name, args=(obj, ))


class MetaSerializer(NonNestedSerializer):
    location = LocationField(source='id', read_only=True)

    def to_representation(self, obj):
        representation = super(MetaSerializer, self).to_representation(obj)
        representation['resourceType'] = self.parent.resource_type
        return representation


class SCIMMemberSerializer(serializers.ModelSerializer):
    resource_schemas = ["urn:ietf:params:scim:schemas:core:2.0:User"]
    resource_type = 'User'
    detail_view_name = 'scim-user-detail'

    externalId = serializers.CharField(source='remote_id')
    name = NameSerializer()
    emails = EmailsField(
        source='email',
        validators=[validators.UniqueValidator(queryset=Member.objects.all())]
    )
    active = serializers.BooleanField(source='is_active')
    groups = serializers.SerializerMethodField(read_only=True)
    schemas = SchemaSerializer(read_only=False)
    meta = MetaSerializer(required=False)

    def get_groups(self, obj):
        return GroupSerializer(
            obj.groups.exclude(
                name='Authenticated'
            ),
            many=True,
            read_only=True
        ).data

    class Meta:
        model = Member
        fields = ('id', 'externalId', 'name', 'emails', 'active', 'groups', 'schemas', 'meta')


class GroupMemberSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='pk')
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

    class Meta:
        model = Member
        fields = ('value', 'ref', 'type')


class SCIMGroupSerializer(serializers.ModelSerializer):
    resource_schemas = ["urn:ietf:params:scim:schemas:core:2.0:Group"]
    resource_type = 'Group'
    detail_view_name = 'scim-group-detail'

    displayName = serializers.CharField(source='name', read_only=True)
    members = GroupMemberSerializer(many=True, source='user_set', read_only=False)
    schemas = SchemaSerializer(read_only=False, required=False)
    meta = MetaSerializer(required=False)

    class Meta:
        model = Group
        fields = ('id', 'displayName', 'schemas', 'meta', 'members', )

    def update(self, obj, data):
        members = data.pop('user_set')
        obj.user_set.clear()
        for member in members:
            try:
                user = Member.objects.get(pk=member['pk'])
                obj.user_set.add(user)
            except Member.DoesNotExist:
                pass

        return super(SCIMGroupSerializer, self).update(obj, data)
