from builtins import object
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model, password_validation, authenticate
from django.contrib.auth.hashers import make_password
from django.core.signing import TimestampSigner
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, exceptions
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework_jwt.settings import api_settings

from bluebottle.bb_projects.models import ProjectTheme
from bluebottle.bluebottle_drf2.serializers import SorlImageField, ImageSerializer
from bluebottle.clients import properties
from bluebottle.geo.models import Location, Place
from bluebottle.geo.serializers import PlaceSerializer
from bluebottle.members.messages import SignUptokenMessage
from bluebottle.members.models import MemberPlatformSettings, UserActivity
from bluebottle.organizations.serializers import OrganizationSerializer
from bluebottle.segments.models import Segment
from bluebottle.segments.serializers import SegmentTypeSerializer
from bluebottle.tasks.models import Skill
from bluebottle.utils.serializers import PermissionField, TruncatedCharField, CaptchaField

try:
    from axes.attempts import is_already_locked
except ImportError:
    is_already_locked = lambda request: request.axes_locked_out

BB_USER_MODEL = get_user_model()


jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class AxesJSONWebTokenSerializer(JSONWebTokenSerializer):
    def validate(self, attrs):
        credentials = {
            self.username_field: attrs.get(self.username_field),
            'password': attrs.get('password')
        }

        if all(credentials.values()):
            request = self.context['request']

            if is_already_locked(request):
                raise exceptions.Throttled(
                    600, 'Too many failed password attempts.'
                )

            user = authenticate(request, **credentials)

            if user:
                if not user.is_active:
                    msg = _('User account is disabled.')
                    raise serializers.ValidationError(msg)

                payload = jwt_payload_handler(user)

                return {
                    'token': jwt_encode_handler(payload),
                    'user': user
                }
            else:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Must include "{username_field}" and "password".')
            msg = msg.format(username_field=self.username_field)
            raise serializers.ValidationError(msg)


class PrivateProfileMixin(object):
    private_fields = (
        'url', 'full_name', 'picture', 'about_me', 'location', 'last_name',
        'phone_number', 'avatar', 'website', 'twitter', 'facebook', 'skypename'
    )

    def to_representation(self, obj):
        data = super(PrivateProfileMixin, self).to_representation(obj)

        user = self.context['request'].user
        can_read_full_profile = self.context['request'].user.has_perm(
            'members.api_read_full_member')

        if obj != user and not can_read_full_profile:
            for field in self.private_fields:
                if field in data:
                    del data[field]

        return data


class BaseUserPreviewSerializer(PrivateProfileMixin, serializers.ModelSerializer):
    """
    Serializer for a subset of a member's public profile. This is usually
    embedded into other serializers.
    """

    def __init__(self, *args, **kwargs):
        kwargs['read_only'] = True
        super(BaseUserPreviewSerializer, self).__init__(*args, **kwargs)

    avatar = SorlImageField('133x133', source='picture', crop='center')

    # TODO: Remove first/last name and only use these
    full_name = serializers.ReadOnlyField(
        source='get_full_name', read_only=True)
    short_name = serializers.ReadOnlyField(
        source='get_short_name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_anonymous = serializers.SerializerMethodField()

    def get_is_anonymous(self, obj):
        return False

    class Meta(object):
        model = BB_USER_MODEL
        fields = ('id', 'first_name', 'last_name', 'initials', 'about_me',
                  'avatar', 'full_name', 'short_name', 'is_active', 'is_anonymous')


class AnonymizedUserPreviewSerializer(PrivateProfileMixin, serializers.ModelSerializer):
    """
    Serializer for a subset of a member's public profile. This is usually
    embedded into other serializers.
    """
    is_anonymous = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        kwargs['read_only'] = True
        super(AnonymizedUserPreviewSerializer, self).__init__(*args, **kwargs)

    id = 0

    def get_is_anonymous(self, obj):
        return False

    class Meta(object):
        model = BB_USER_MODEL
        fields = ('id', 'is_anonymous')


class UserPreviewSerializer(serializers.ModelSerializer):
    """
    User preview serializer that respects anonymization_age
    """

    def to_representation(self, instance):
        if self.parent.__class__.__name__ == 'ReactionSerializer':
            # For some reason self.parent.instance doesn't work on ReactionSerializer
            if self.parent.instance:
                if self.parent.instance.anonymized:
                    return {"id": 0, "is_anonymous": True}
            else:
                wallpost = self.parent.parent.parent.instance
                if wallpost.anonymized:
                    return {"id": 0, "is_anonymous": True}
        if self.parent and self.parent.instance and getattr(self.parent.instance, 'anonymized', False):
            return {"id": 0, "is_anonymous": True}
        return BaseUserPreviewSerializer(instance, context=self.context).to_representation(instance)

    class Meta(object):
        model = BB_USER_MODEL
        fields = (
            'id',
            'first_name',
            'last_name',
            'initials',
            'about_me',
            'avatar',
            'full_name',
            'short_name',
            'is_active'
        )


class UserPermissionsSerializer(serializers.Serializer):
    def get_attribute(self, obj):
        return obj

    project_list = PermissionField('initiative-list')
    project_manage_list = PermissionField('initiative-list')
    homepage = PermissionField('homepage', view_args=('primary_language', ))

    class Meta(object):
        fields = [
            'project_list',
            'project_manage_list',
            'homepage'
        ]


class CurrentUserSerializer(BaseUserPreviewSerializer):
    """
    Serializer for the current authenticated user. This is the same as the
    serializer for the member preview with the
    addition of id_for_ember.
    """
    # This is a hack to work around an issue with Ember-Data keeping the id as
    # 'current'.
    id_for_ember = serializers.IntegerField(source='id', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    permissions = UserPermissionsSerializer(read_only=True)
    organization = OrganizationSerializer(
        read_only=True, source='partner_organization')

    class Meta(object):
        model = BB_USER_MODEL
        fields = UserPreviewSerializer.Meta.fields + (
            'id_for_ember', 'primary_language', 'email', 'full_name', 'phone_number',
            'last_login', 'date_joined', 'location',
            'verified', 'permissions', 'matching_options_set',
            'organization'
        )


class OldSegmentSerializer(serializers.ModelSerializer):

    type = SegmentTypeSerializer()

    class Meta(object):
        model = Segment
        fields = (
            'id', 'name', 'type'
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

    is_active = serializers.BooleanField(read_only=True)

    segments = OldSegmentSerializer(many=True, read_only=True)

    class Meta(object):
        model = BB_USER_MODEL
        fields = (
            'id', 'url', 'full_name', 'short_name', 'initials', 'picture',
            'primary_language', 'about_me', 'location', 'avatar', 'date_joined',
            'is_active', 'website', 'twitter', 'facebook',
            'skypename', 'skill_ids', 'favourite_theme_ids',
            'subscribed', 'segments'
        )


class UserActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for user activity (log paths)
    """
    path = TruncatedCharField(length=200, required=False)

    class Meta(object):
        model = UserActivity
        fields = (
            'id',
            'path',
        )


class ManageProfileSerializer(UserProfileSerializer):
    """
    Serializer for the a member's private profile.
    """
    partial = True
    from_facebook = serializers.SerializerMethodField()
    place = PlaceSerializer(required=False, allow_null=True)

    def get_from_facebook(self, instance):
        try:
            instance.social_auth.get(provider='facebook')
            return True
        except instance.social_auth.model.DoesNotExist:
            return False

    class Meta(object):
        model = BB_USER_MODEL
        fields = UserProfileSerializer.Meta.fields + (
            'email', 'newsletter', 'campaign_notifications', 'matching_options_set', 'location',
            'birthdate', 'gender', 'first_name', 'last_name', 'phone_number',
            'from_facebook', 'place',
        )

    def update(self, instance, validated_data):
        place = validated_data.pop('place', None)
        if place:
            if instance.place:
                current_place = instance.place
                for key, value in list(place.items()):
                    setattr(current_place, key, value)
                current_place.save()
            else:
                Place.objects.create(content_object=instance, **place)
        else:
            if instance.place:
                instance.place.delete()

        return super(ManageProfileSerializer, self).update(instance, validated_data)


class UserDataExportSerializer(UserProfileSerializer):
    """
    Serializer for the a member's data dump.
    """

    class Meta(object):
        model = BB_USER_MODEL
        fields = (
            'id', 'email', 'location', 'birthdate',
            'url', 'full_name', 'short_name', 'initials', 'picture',
            'gender', 'first_name', 'last_name', 'phone_number',
            'primary_language', 'about_me', 'location', 'avatar',
            'date_joined', 'website', 'twitter', 'facebook',
            'skypename', 'skills', 'favourite_themes'
        )


class PasswordValidator(object):
    def set_context(self, field):
        if field.parent.instance:
            self.user = field.parent.instance
        else:
            self.user = None

    def __call__(self, value):
        password_validation.validate_password(value, self.user)
        return value


# Thanks to Neamar Tucote for this code:
# https://groups.google.com/d/msg/django-rest-framework/abMsDCYbBRg/d2orqUUdTqsJ
class PasswordField(serializers.CharField):
    """ Special field to update a password field. """
    widget = forms.widgets.PasswordInput
    hidden_password_string = '********'

    def __init__(self, **kwargs):
        super(PasswordField, self).__init__(**kwargs)
        validator = PasswordValidator()
        self.validators.append(validator)

    def to_representation(self, value):
        """ Hide hashed-password in API display. """
        return self.hidden_password_string


class SignUpTokenSerializer(serializers.ModelSerializer):
    """
    Serializer for creating users. This can only be used for creating
    users (POST) and should not be used for listing,
    editing or viewing users.
    """
    email = serializers.EmailField(max_length=254)

    class Meta(object):
        model = BB_USER_MODEL
        fields = ('id', 'email')

    def validate_email(self, email):
        settings = MemberPlatformSettings.objects.get()
        if (
            settings.email_domain and
            not email.endswith('@{}'.format(settings.email_domain))
        ):
            raise serializers.ValidationError(
                ('Only emails for the domain {} are allowed').format(
                    settings.email_domain)
            )

        if len(BB_USER_MODEL.objects.filter(email=email, is_active=True)):
            raise serializers.ValidationError('member with this email address already exists.')

        return email

    def create(self, validated_data):
        (instance, _) = BB_USER_MODEL.objects.get_or_create(
            email=validated_data['email'], defaults={'is_active': False}
        )
        token = TimestampSigner().sign(instance.pk)
        SignUptokenMessage(instance, custom_message=token).compose_and_send()

        return instance


class SignUpTokenConfirmationSerializer(serializers.ModelSerializer):
    """
    Serializer for creating users. This can only be used for creating
    users (POST) and should not be used for listing,
    editing or viewing users.
    """
    password = PasswordField(required=True, max_length=128)
    jwt_token = serializers.CharField(source='get_jwt_token', read_only=True)

    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)

    class Meta(object):
        model = BB_USER_MODEL
        fields = ('id', 'password', 'jwt_token', 'first_name', 'last_name', )

    def validate_password(self, password):
        return make_password(password)


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating users. This can only be used for creating
    users (POST) and should not be used for listing,
    editing or viewing users.
    """
    email_confirmation = serializers.EmailField(
        label=_('password_confirmation'), max_length=254, required=False)
    password = PasswordField(required=True, max_length=128)
    token = serializers.CharField(required=False, max_length=128)
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
                settings.REST_FRAMEWORK.get(
                    'NON_FIELD_ERRORS_KEY', 'non_field_errors')
            ] = [conflict]

        return errors

    def validate(self, data):
        if 'email_confirmation' in data and data['email'] != data['email_confirmation']:
            raise serializers.ValidationError(_('Email confirmation mismatch'))

        settings = MemberPlatformSettings.objects.get()

        if settings.confirm_signup:
            raise serializers.ValidationError(
                {'token': _('Signup requires a confirmation token')})

        data['password'] = make_password(data['password'])

        return data

    class Meta(object):
        model = BB_USER_MODEL
        fields = ('id', 'first_name', 'last_name', 'email_confirmation',
                  'email', 'password', 'token', 'jwt_token', 'primary_language')


class PasswordResetSerializer(serializers.Serializer):
    """
    Password reset request serializer that uses the email validation from the
    Django PasswordResetForm.
    """
    email = serializers.EmailField(required=True, max_length=254)

    class Meta(object):
        fields = ('email',)


class PasswordProtectedMemberSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, max_length=128
    )
    jwt_token = serializers.CharField(source='get_jwt_token', read_only=True)

    class Meta(object):
        model = BB_USER_MODEL
        fields = ('password', 'jwt_token')


class EmailSetSerializer(PasswordProtectedMemberSerializer):
    class Meta(PasswordProtectedMemberSerializer.Meta):
        fields = ('email', ) + PasswordProtectedMemberSerializer.Meta.fields


class PasswordUpdateSerializer(PasswordProtectedMemberSerializer):
    new_password = PasswordField(
        write_only=True, required=True, max_length=128)

    def save(self):
        self.instance.set_password(self.validated_data['new_password'])
        self.instance.save()

    class Meta(PasswordProtectedMemberSerializer.Meta):
        fields = ('new_password', ) + \
            PasswordProtectedMemberSerializer.Meta.fields


class PasswordSetSerializer(serializers.Serializer):
    """
    We can't use the PasswordField here because it hashes the passwords with
    a salt which means we can't compare the
    two passwords to see if they are the same.
    """
    new_password1 = PasswordField(required=True, max_length=128)
    new_password2 = serializers.CharField(required=True, max_length=128)

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError(
                _('The two password fields didn\'t match.'))

        return data

    class Meta(object):
        fields = ('new_password1', 'new_password2')


class UserVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()
    id = serializers.SerializerMethodField()

    def get_id(self, obj):
        return self.context['request'].user.id


class MemberPlatformSettingsSerializer(serializers.ModelSerializer):
    background = SorlImageField('1408x1080', crop='center')

    class Meta(object):
        model = MemberPlatformSettings
        fields = (
            'require_consent',
            'consent_link',
            'closed',
            'email_domain',
            'confirm_signup',
            'login_methods',
            'background',
        )


class TokenLoginSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    token = serializers.CharField(required=True)


class CaptchaSerializer(serializers.Serializer):
    token = CaptchaField(required=True)
