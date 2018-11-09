from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from bluebottle.bb_accounts.models import UserAddress
from bluebottle.bb_projects.models import ProjectTheme
from bluebottle.bluebottle_drf2.serializers import SorlImageField, ImageSerializer
from bluebottle.clients import properties
from bluebottle.geo.models import Location
from bluebottle.geo.serializers import LocationSerializer, CountrySerializer
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.projects.models import Project
from bluebottle.donations.models import Donation
from bluebottle.tasks.models import Skill, Task, TaskMember
from bluebottle.utils.serializers import PermissionField
from bluebottle.organizations.serializers import OrganizationPreviewSerializer

BB_USER_MODEL = get_user_model()


class PrivateProfileMixin(object):
    private_fields = (
        'url', 'full_name', 'picture', 'about_me', 'location', 'last_name',
        'phone_number', 'avatar', 'website', 'twitter', 'facebook', 'skypename'
    )

    def to_representation(self, obj):
        data = super(PrivateProfileMixin, self).to_representation(obj)

        user = self.context['request'].user
        can_read_full_profile = self.context['request'].user.has_perm('members.api_read_full_member')

        if obj != user and not can_read_full_profile:
            for field in self.private_fields:
                if field in data:
                    del data[field]

        return data


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ('id', 'line1', 'line2', 'address_type',
                  'city', 'state', 'country', 'postal_code')


class UserPreviewSerializer(PrivateProfileMixin, serializers.ModelSerializer):
    """
    Serializer for a subset of a member's public profile. This is usually
    embedded into other serializers.
    """

    def __init__(self, *args, **kwargs):
        kwargs['read_only'] = True
        super(UserPreviewSerializer, self).__init__(*args, **kwargs)

    avatar = SorlImageField('133x133', source='picture', crop='center')

    # TODO: Remove first/last name and only use these
    full_name = serializers.ReadOnlyField(source='get_full_name', read_only=True)
    short_name = serializers.ReadOnlyField(source='get_short_name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = BB_USER_MODEL
        fields = ('id', 'first_name', 'last_name', 'initials',
                  'avatar', 'full_name', 'short_name', 'is_active')


class UserPermissionsSerializer(serializers.Serializer):
    def get_attribute(self, obj):
        return obj

    project_list = PermissionField('project_list')
    project_manage_list = PermissionField('project_manage_list')
    homepage = PermissionField('homepage', view_args=('primary_language', ))

    class Meta:
        fields = [
            'project_list',
            'project_manage_list',
            'homepage'
        ]


class CurrentUserSerializer(UserPreviewSerializer):
    """
    Serializer for the current authenticated user. This is the same as the
    serializer for the member preview with the
    addition of id_for_ember.
    """
    # This is a hack to work around an issue with Ember-Data keeping the id as
    # 'current'.
    id_for_ember = serializers.IntegerField(source='id', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    country = CountrySerializer(source='address.country')
    location = LocationSerializer()
    permissions = UserPermissionsSerializer(read_only=True)
    partner_organization = OrganizationPreviewSerializer(allow_null=True, read_only=True, required=False)

    class Meta:
        model = BB_USER_MODEL
        fields = UserPreviewSerializer.Meta.fields + (
            'id_for_ember', 'primary_language', 'email', 'full_name', 'phone_number',
            'last_login', 'date_joined', 'task_count', 'project_count',
            'has_projects', 'donation_count', 'fundraiser_count', 'location',
            'country', 'verified', 'permissions', 'partner_organization',
        )


class UserProfileSerializer(PrivateProfileMixin, serializers.ModelSerializer):
    """
    Serializer for a member's public profile.
    """
    url = serializers.HyperlinkedIdentityField(view_name='user-profile-detail',
                                               lookup_field='pk')
    picture = ImageSerializer(required=False)
    date_joined = serializers.DateTimeField(read_only=True)

    full_name = serializers.CharField(source='get_full_name', read_only=True)
    short_name = serializers.CharField(source='get_short_name', read_only=True)

    primary_language = serializers.CharField(required=False,
                                             default=properties.LANGUAGE_CODE)
    location = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                                  queryset=Location.objects)
    avatar = SorlImageField('133x133', source='picture', crop='center',
                            required=False)

    skill_ids = serializers.PrimaryKeyRelatedField(many=True,
                                                   source='skills',
                                                   required=False,
                                                   queryset=Skill.objects)
    favourite_theme_ids = serializers.PrimaryKeyRelatedField(
        many=True, source='favourite_themes', queryset=ProjectTheme.objects)

    project_count = serializers.ReadOnlyField()
    donation_count = serializers.ReadOnlyField()
    fundraiser_count = serializers.ReadOnlyField()
    task_count = serializers.ReadOnlyField()
    time_spent = serializers.ReadOnlyField()
    tasks_performed = serializers.ReadOnlyField()
    partner_organization = OrganizationPreviewSerializer(allow_null=True, read_only=True, required=False)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = BB_USER_MODEL
        fields = (
            'id', 'url', 'full_name', 'short_name', 'initials', 'picture',
            'primary_language', 'about_me', 'location', 'avatar',
            'project_count', 'donation_count', 'date_joined',
            'fundraiser_count', 'task_count', 'time_spent', 'is_active',
            'tasks_performed', 'website', 'twitter', 'facebook',
            'skypename', 'skill_ids', 'favourite_theme_ids', 'partner_organization',
        )


class ManageProfileSerializer(UserProfileSerializer):
    """
    Serializer for the a member's private profile.
    """
    partial = True
    address = UserAddressSerializer(allow_null=True)
    from_facebook = serializers.SerializerMethodField()

    def get_from_facebook(self, instance):
        try:
            instance.social_auth.get(provider='facebook')
            return True
        except instance.social_auth.model.DoesNotExist:
            return False

    class Meta:
        model = BB_USER_MODEL
        fields = UserProfileSerializer.Meta.fields + (
            'email', 'address', 'newsletter', 'campaign_notifications', 'location',
            'birthdate', 'gender', 'first_name', 'last_name', 'phone_number',
            'from_facebook',
        )

    def update(self, instance, validated_data):
        address = validated_data.pop('address', {})
        for attr, value in address.items():
            setattr(instance.address, attr, value)

        instance.address.save()

        return super(ManageProfileSerializer, self).update(instance, validated_data)


class UserDataExportSerializer(UserProfileSerializer):
    """
    Serializer for the a member's data dump.
    """
    address = UserAddressSerializer(allow_null=True)

    tasks = serializers.SerializerMethodField()
    projects = serializers.SerializerMethodField()
    task_members = serializers.SerializerMethodField()
    donations = serializers.SerializerMethodField()

    def get_tasks(self, obj):
        from bluebottle.tasks.serializers import MyTasksSerializer

        tasks = Task.objects.filter(author=obj)
        return MyTasksSerializer(
            tasks, many=True, context=self.context
        ).to_representation(tasks)

    def get_projects(self, obj):
        from bluebottle.projects.serializers import ProjectSerializer

        projects = Project.objects.filter(owner=obj)
        return ProjectSerializer(
            projects, many=True, context=self.context
        ).to_representation(projects)

    def get_task_members(self, obj):
        from bluebottle.tasks.serializers import MyTaskMemberSerializer

        task_members = TaskMember.objects.filter(member=obj)
        return MyTaskMemberSerializer(
            task_members, many=True, context=self.context
        ).to_representation(task_members)

    def get_donations(self, obj):
        from bluebottle.donations.serializers import ManageDonationSerializer

        donations = Donation.objects.filter(order__user=obj)
        return ManageDonationSerializer(
            donations, many=True, context=self.context
        ).to_representation(donations)

    class Meta:
        model = BB_USER_MODEL
        fields = (
            'id', 'email', 'address', 'location', 'birthdate',
            'url', 'full_name', 'short_name', 'initials', 'picture',
            'gender', 'first_name', 'last_name', 'phone_number',
            'primary_language', 'about_me', 'location', 'avatar',
            'project_count', 'donation_count', 'date_joined',
            'fundraiser_count', 'task_count', 'time_spent',
            'tasks_performed', 'website', 'twitter', 'facebook',
            'skypename', 'skills', 'favourite_themes',
            'projects', 'tasks', 'task_members', 'donations'
        )


# Thanks to Neamar Tucote for this code:
# https://groups.google.com/d/msg/django-rest-framework/abMsDCYbBRg/d2orqUUdTqsJ
class PasswordField(serializers.CharField):
    """ Special field to update a password field. """
    widget = forms.widgets.PasswordInput
    hidden_password_string = '********'

    def to_internal_value(self, value):
        """ Hash if new value sent, else retrieve current password. """
        from django.contrib.auth.hashers import make_password

        if value == self.hidden_password_string or value == '':
            return self.parent.object.password
        else:
            return make_password(value)

    def to_representation(self, value):
        """ Hide hashed-password in API display. """
        return self.hidden_password_string


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating users. This can only be used for creating
    users (POST) and should not be used for listing,
    editing or viewing users.
    """
    email_confirmation = serializers.EmailField(
        label=_('password_confirmation'), max_length=254, required=False)
    password = PasswordField(required=True, max_length=128)
    jwt_token = serializers.CharField(source='get_jwt_token', read_only=True)
    primary_language = serializers.CharField(required=False)

    @property
    def errors(self):
        errors = super(UserCreateSerializer, self).errors

        if 'email' in errors and 'email' in self.data:
            user = self.Meta.model.objects.get(email=self.data['email'])

            conflict = {
                'email': user.email,
                'id': user.id
            }

            # We assume if they have a social auth associated then they use it
            if user.social_auth.count() > 0:
                social_auth = user.social_auth.all()[0]
                conflict['provider'] = social_auth.provider
                conflict['type'] = 'social'
            else:
                conflict['type'] = 'email'

            errors[
                settings.REST_FRAMEWORK.get('NON_FIELD_ERRORS_KEY', 'non_field_errors')
            ] = [conflict]

        return errors

    def validate(self, data):
        if 'email_confirmation' in data and data['email'] != data['email_confirmation']:
            raise serializers.ValidationError(_('Email confirmation mismatch'))

        return data

    class Meta:
        model = BB_USER_MODEL
        fields = ('id', 'first_name', 'last_name', 'email_confirmation',
                  'email', 'password', 'jwt_token', 'primary_language')


class PasswordResetSerializer(serializers.Serializer):
    """
    Password reset request serializer that uses the email validation from the
    Django PasswordResetForm.
    """
    email = serializers.EmailField(required=True, max_length=254)

    class Meta:
        fields = ('email',)


class PasswordSetSerializer(serializers.Serializer):
    """
    We can't use the PasswordField here because it hashes the passwords with
    a salt which means we can't compare the
    two passwords to see if they are the same.
    """
    new_password1 = serializers.CharField(required=True, max_length=128)
    new_password2 = serializers.CharField(required=True, max_length=128)

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError(_('The two password fields didn\'t match.'))

        return data

    class Meta:
        fields = ('new_password1', 'new_password2')


class UserVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()
    id = serializers.SerializerMethodField()

    def get_id(self, obj):
        return self.context['request'].user.id


class MemberPlatformSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberPlatformSettings
        fields = (
            'require_consent',
            'consent_link',
        )


class TokenLoginSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    token = serializers.CharField(required=True)
