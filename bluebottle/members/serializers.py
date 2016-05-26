from bluebottle.bb_accounts.models import UserAddress
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import (
    SorlImageField, ImageSerializer)

from bluebottle.clients import properties
from bluebottle.tasks.models import Skill
from bluebottle.geo.models import Location
from bluebottle.bb_projects.models import ProjectTheme
from bluebottle.geo.serializers import LocationSerializer, CountrySerializer
from bluebottle.geo.models import Location
from bluebottle.tasks.models import Skill
from bluebottle.bb_projects.models import ProjectTheme

BB_USER_MODEL = get_user_model()


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ('id', 'line1', 'line2', 'address_type',
                  'city', 'state', 'country', 'postal_code')


class UserPreviewSerializer(serializers.ModelSerializer):
    """
    Serializer for a subset of a member's public profile. This is usually
    embedded into other serializers.
    """

    def __init__(self, *args, **kwargs):
        kwargs['read_only'] = True
        super(UserPreviewSerializer, self).__init__(*args, **kwargs)

    avatar = SorlImageField('picture', '133x133', crop='center')

    # TODO: Remove first/last name and only use these
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    short_name = serializers.CharField(source='get_short_name', read_only=True)

    class Meta:
        model = BB_USER_MODEL
        fields = ('id', 'first_name', 'last_name', 'username',
                  'avatar', 'full_name', 'short_name')


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

    class Meta:
        model = BB_USER_MODEL
        fields = UserPreviewSerializer.Meta.fields + (
            'id_for_ember', 'primary_language', 'email', 'full_name',
            'last_login', 'date_joined', 'task_count', 'project_count',
            'has_projects', 'donation_count', 'fundraiser_count', 'location',
            'country')




class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for a member's public profile.
    """
    url = serializers.HyperlinkedIdentityField(view_name='user-profile-detail',
                                               lookup_field='pk')
    picture = ImageSerializer(required=False)
    date_joined = serializers.DateTimeField(read_only=True)

    # TODO: Remove first/last name and only use these
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    short_name = serializers.CharField(source='get_short_name', read_only=True)

    primary_language = serializers.CharField(required=False,
                                             default=properties.LANGUAGE_CODE)
    location = serializers.PrimaryKeyRelatedField(required=False,
                                                  queryset=Location.objects)
    avatar = SorlImageField('picture', '133x133', crop='center',
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

    class Meta:
        model = BB_USER_MODEL
        fields = ('id', 'url', 'full_name', 'short_name', 'picture',
                  'primary_language', 'about_me', 'location', 'avatar',
                  'project_count', 'donation_count', 'date_joined',
                  'fundraiser_count', 'task_count', 'time_spent',
                  'tasks_performed', 'website', 'twitter', 'facebook',
                  'skypename', 'skill_ids', 'favourite_theme_ids')

    def save_object(self, obj, **kwargs):
        """ Make sure that we can set None as the address.

        We should be able to solve this by adding `allow_null`
        to the address field,
        however our version of drf does not support that.

        FIXME: fix the above after drf upgrade.
        """
        if 'address' in obj._related_data and \
                obj._related_data['address'] is None:
            del obj._related_data['address']

        return super(UserProfileSerializer, self).save_object(obj, **kwargs)


class ManageProfileSerializer(UserProfileSerializer):
    """
    Serializer for the a member's private profile.
    """

    class Meta:
        model = BB_USER_MODEL
        fields = UserProfileSerializer.Meta.fields + (
            'email', 'address', 'newsletter', 'campaign_notifications',
            'birthdate', 'gender', 'first_name', 'last_name', 'username'
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
    email = serializers.EmailField(required=True, max_length=254)
    email_confirmation = serializers.EmailField(
        label=_('password_confirmation'), max_length=254)
    password = PasswordField(required=True, max_length=128)
    username = serializers.CharField(read_only=True)
    jwt_token = serializers.CharField(source='get_jwt_token', read_only=True)
    primary_language = serializers.CharField(required=False)

    def validate_email_confirmation(self, attrs, source):
        """
        email_confirmation check
        """
        email_confirmation = attrs[source]
        email = attrs['email']

        if email_confirmation != email:
            raise serializers.ValidationError(_('Email confirmation mismatch'))

        return attrs

    class Meta:
        model = BB_USER_MODEL
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'password', 'jwt_token', 'primary_language')
        non_native_fields = ('email_confirmation',)


class PasswordResetSerializer(serializers.Serializer):
    """
    Password reset request serializer that uses the email validation from the
    Django PasswordResetForm.
    """
    email = serializers.EmailField(required=True, max_length=254)

    class Meta:
        fields = ('email',)

    def __init__(self, password_reset_form=None, *args, **kwargs):
        self.password_reset_form = password_reset_form
        super(PasswordResetSerializer, self).__init__(*args, **kwargs)

    def validate_email(self, attrs, source):
        # Don't need this check in newer versions of DRF2.
        if attrs is not None:
            value = attrs[source]
            self.password_reset_form.cleaned_data = {"email": value}
            return self.password_reset_form.clean_email()


class PasswordSetSerializer(serializers.Serializer):
    """
    A serializer that lets a user change set his/her password without entering
    the old password. This uses the validation from the Django SetPasswordForm.

    We can't use the PasswordField here because it hashes the passwords with
    a salt which means we can't compare the
    two passwords to see if they are the same.
    """
    new_password1 = serializers.CharField(
        required=True, max_length=128)
    new_password2 = serializers.CharField(
        required=True, max_length=128)

    class Meta:
        fields = ('new_password1', 'new_password2')

    def __init__(self, password_set_form=None, *args, **kwargs):
        self.password_set_form = password_set_form
        super(PasswordSetSerializer, self).__init__(*args, **kwargs)

    def validate_new_password2(self, attrs, source):
        # Don't need this check in newer versions of DRF2.
        if attrs is not None:
            value = attrs[source]
            self.password_set_form.cleaned_data = {
                "new_password1": attrs['new_password1'],
                "new_password2": value}
            return self.password_set_form.clean_new_password2()
