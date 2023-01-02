import uuid
from builtins import object

import passwordmeter
from axes.handlers.proxy import AxesProxyHandler
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model, password_validation, authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, exceptions, validators
from rest_framework_json_api.serializers import Serializer
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework_jwt.settings import api_settings

from bluebottle.bluebottle_drf2.serializers import SorlImageField, ImageSerializer
from bluebottle.clients import properties
from bluebottle.geo.models import Location, Place
from bluebottle.geo.serializers import PlaceSerializer
from bluebottle.initiatives.models import Theme
from bluebottle.members.models import MemberPlatformSettings, UserActivity, UserSegment
from bluebottle.organizations.serializers import OrganizationSerializer
from bluebottle.segments.models import Segment
from bluebottle.segments.serializers import SegmentTypeSerializer
from bluebottle.time_based.models import Skill
from bluebottle.utils.serializers import PermissionField, TruncatedCharField, CaptchaField

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

            user = authenticate(request, **credentials)

            if getattr(request, 'axes_locked_out', False):
                raise exceptions.Throttled(
                    600, 'Too many failed password attempts.'
                )

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


class PasswordValidator(object):
    requires_context = True

    def __call__(self, value, serializer_field):
        if serializer_field.parent.instance:
            user = serializer_field.parent.instance
        else:
            user = None

        password_validation.validate_password(value, user)
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


class AuthTokenSerializer(Serializer, AxesJSONWebTokenSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['email'] = serializers.CharField(
            required=True
        )
    email = serializers.CharField(required=True)
    password = PasswordField(required=True)
    token = serializers.CharField(read_only=True)

    class Meta:
        fields = ['token', 'email', 'password']

    class JSONAPIMeta(object):
        resource_name = 'auth/token'


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

    def __init__(self, *args, **kwargs):
        self.hide_last_name = kwargs.pop('hide_last_name', None)

        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        user = self.context['request'].user
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

        representation = BaseUserPreviewSerializer(instance, context=self.context).to_representation(instance)
        if not (
            user.is_staff or
            user.is_superuser
        ) and (
            self.hide_last_name and
            MemberPlatformSettings.objects.get().display_member_names == 'first_name'
        ):
            del representation['last_name']
            representation['full_name'] = representation['first_name']

        return representation

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
    homepage = PermissionField('home-page-detail')

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
        read_only=True, source='partner_organization'
    )
    segments = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Segment.objects
    )
    has_initiatives = serializers.SerializerMethodField()

    def get_has_initiatives(self, obj):
        return obj.own_initiatives.exists()

    class Meta(object):
        model = BB_USER_MODEL
        fields = UserPreviewSerializer.Meta.fields + (
            'id_for_ember', 'primary_language', 'email', 'full_name', 'phone_number',
            'last_login', 'date_joined', 'location',
            'verified', 'permissions', 'matching_options_set',
            'organization', 'segments', 'required', 'has_initiatives',
            'hours_spent', 'hours_planned'
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
        many=True, source='favourite_themes', queryset=Theme.objects)

    segments = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Segment.objects
    )

    is_active = serializers.BooleanField(read_only=True)

    def save(self, *args, **kwargs):

        instance = super().save(*args, **kwargs)

        if 'location' in self.validated_data:
            # if we are setting the location, make sure we verify the location too
            instance.location_verified = True
            instance.save()

        if 'segments' in self.validated_data:
            # if we are setting segments, make sure we verify them too
            UserSegment.objects.filter(member_id=instance.pk).update(verified=True)

        return instance

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
    Serializer for the member's private profile.
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
            'email', 'newsletter', 'campaign_notifications', 'receive_reminder_emails',
            'matching_options_set', 'location',
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
                instance.place = Place.objects.create(**place)
        else:
            if instance.place:
                instance.place = None

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


class SignUpTokenSerializer(serializers.ModelSerializer):
    """
    Serializer for creating users. This can only be used for creating
    users (POST) and should not be used for listing,
    editing or viewing users.
    """
    email = serializers.EmailField(max_length=254)
    url = serializers.CharField(required=False, allow_blank=True)
    segment_id = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        (instance, _) = BB_USER_MODEL.objects.get_or_create(
            email__iexact=validated_data['email'],
            defaults={'is_active': False, 'email': validated_data['email']}
        )
        return instance

    class Meta(object):
        model = BB_USER_MODEL
        fields = ('id', 'email', 'url', 'segment_id')

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

        if len(BB_USER_MODEL.objects.filter(email__iexact=email, is_active=True)):
            raise serializers.ValidationError(
                'A member with this email address already exists.',
                code='email_in_use',
            )
        return email

    class JSONAPIMeta:
        resource_name = 'signup-tokens'


class SignUpTokenConfirmationSerializer(serializers.ModelSerializer):
    """
    Serializer for creating users. This can only be used for creating
    users (POST) and should not be used for listing,
    editing or viewing users.
    """
    password = PasswordField(required=True, max_length=128)
    token = serializers.CharField(required=True, max_length=128)
    jwt_token = serializers.CharField(source='get_jwt_token', read_only=True)

    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)

    class Meta(object):
        model = BB_USER_MODEL
        fields = ('id', 'password', 'token', 'jwt_token', 'first_name', 'last_name', )

    def validate_password(self, password):
        return make_password(password)

    class JSONAPIMeta:
        resource_name = 'signup-token-confirmations'


class PasswordStrengthSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.CharField(write_only=True, allow_blank=True, required=False)
    strength = serializers.SerializerMethodField()

    def validate(self, data):
        user = BB_USER_MODEL(**data)
        validate_password(data['password'], user)
        return data

    def get_strength(self, data):
        strength, _ = passwordmeter.test(self.validated_data['password'])
        return strength

    class Meta(object):
        model = BB_USER_MODEL
        fields = ('id', 'password', 'email', 'strength')

    class JSONAPIMeta:
        resource_name = 'password-strengths'


class UniqueEmailValidator(validators.UniqueValidator):
    message = _('An user with this email address already exists')

    def __call__(self, value, serializer_field):
        try:
            return super().__call__(value, serializer_field)
        except serializers.ValidationError:
            user = BB_USER_MODEL.objects.get(email__iexact=value)
            if user.social_auth.count() > 0:
                code = 'social_account_unique'
            else:
                code = 'email_unique'

            raise serializers.ValidationError(self.message, code=code)


class MemberSignUpSerializer(serializers.ModelSerializer):
    """
    Serializer for creating users. This can only be used for creating
    users (POST) and should not be used for listing,
    editing or viewing users.
    """
    email = serializers.EmailField(
        max_length=254,
        validators=[
            UniqueEmailValidator(
                queryset=BB_USER_MODEL.objects.all(), lookup='iexact'
            )
        ]
    )
    password = PasswordField(required=True, max_length=128)
    token = serializers.CharField(source='get_jwt_token', read_only=True)

    @property
    def errors(self):
        return super(MemberSignUpSerializer, self).errors

    def validate(self, data):
        settings = MemberPlatformSettings.objects.get()
        if settings.confirm_signup:
            raise serializers.ValidationError(
                {'email': _('Signup requires a confirmation token.')}
            )

        if settings.closed:
            raise serializers.ValidationError(
                {'email': _('The platform is closed.')}
            )

        passwordmeter.test(data['password'])
        data['password'] = make_password(data['password'])
        return data

    class Meta(object):
        model = BB_USER_MODEL
        fields = ('id', 'first_name', 'last_name', 'email', 'password', 'token', )

    class JSONAPIMeta:
        resource_name = 'auth/signup'


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating users. This can only be used for creating
    users (POST) and should not be used for listing,
    editing or viewing users.
    """
    email = serializers.EmailField(
        max_length=254,
        validators=[
            validators.UniqueValidator(
                queryset=BB_USER_MODEL.objects.all(), lookup='iexact'
            )
        ]
    )
    email_confirmation = serializers.EmailField(
        label=_('email_confirmation'), max_length=254, required=False)
    password = PasswordField(required=True, max_length=128)
    token = serializers.CharField(required=False, max_length=128)
    jwt_token = serializers.CharField(source='get_jwt_token', read_only=True)
    primary_language = serializers.CharField(required=False)

    @property
    def errors(self):
        errors = super(UserCreateSerializer, self).errors

        if 'email' in errors and 'email' in self.data and errors['email'][0].code == 'unique':
            user = self.Meta.model.objects.get(email__iexact=self.data['email'])

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

            request = self.context['request']
            AxesProxyHandler.user_login_failed(self, {}, request)
            if getattr(request, 'axes_locked_out', False):
                raise exceptions.Throttled(
                    600, 'Too many failed registration attempts.'
                )
            del errors['email']

        return errors

    def validate(self, data):
        if 'email_confirmation' in data:
            if data['email'] != data['email_confirmation']:
                raise serializers.ValidationError(_('Email confirmation mismatch'))
            del data['email_confirmation']

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
        fields = ('id', 'email',)

    class JSONAPIMeta(object):
        resource_name = 'reset-tokens'


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, max_length=254)
    password = PasswordField(required=True, max_length=254)
    jwt_token = serializers.CharField(read_only=True)

    class Meta(object):
        fields = ('token', 'jwt_token', 'password')

    class JSONAPIMeta(object):
        resource_name = 'reset-token-confirmations'


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
            'session_only',
            'confirm_signup',
            'login_methods',
            'background',
            'enable_gender',
            'enable_address',
            'enable_birthdate',
            'required_questions_location',
            'require_office',
            'verify_office',
            'require_address',
            'require_birthdate',
            'require_phone_number',
            'create_initiatives',
            'do_good_hours',
            'fiscal_month_offset',
            'fiscal_year',
            'fiscal_year_start',
            'fiscal_year_end',
        )


class TokenLoginSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    token = serializers.CharField(required=True)


class CaptchaSerializer(serializers.Serializer):
    token = CaptchaField(required=True)
    id = serializers.SerializerMethodField()

    def get_id(self, obj):
        return str(uuid.uuid4())

    class Meta(object):
        fields = ('id', 'token')

    class JSONAPIMeta:
        resource_name = 'captcha-tokens'
