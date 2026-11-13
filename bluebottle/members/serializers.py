import uuid
from builtins import object

import passwordmeter
from django import forms
from django.contrib.auth import get_user_model, password_validation, authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, exceptions, validators
from rest_framework_json_api.serializers import (
    Serializer, ModelSerializer, ResourceRelatedField, PolymorphicModelSerializer
)
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework_jwt.settings import api_settings

from bluebottle.bluebottle_drf2.serializers import SorlImageField
from bluebottle.clients import properties
from bluebottle.files.serializers import ImageField
from bluebottle.geo.models import Location, Place
from bluebottle.geo.serializers import OldPlaceSerializer
from bluebottle.initiatives.models import Theme
from bluebottle.members.models import (
    MemberPlatformSettings, UserActivity, UserSegment, Member,
    AuthenticationMethod, PasswordAuthentication, FacebookAuthentication,
    GoogleAuthentication, SAMLAuthentication
)
from bluebottle.segments.models import Segment
from bluebottle.segments.serializers import SegmentTypeSerializer
from bluebottle.time_based.models import Skill
from bluebottle.utils.serializers import PermissionField, TruncatedCharField, CaptchaField, UserPermissionField

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
                msg = _(
                    'We are unable to log you in with the provided email address and password combination.'
                )
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

    def __init__(self, validate=True, **kwargs):
        super(PasswordField, self).__init__(**kwargs)
        if validate:
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
    password = PasswordField(required=True, validate=False)
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
    can_pledge = serializers.BooleanField(read_only=True)
    can_do_bank_transfer = serializers.BooleanField(read_only=True)

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
        fields = (
            'id', 'first_name', 'last_name', 'initials', 'about_me',
            'avatar', 'full_name', 'short_name',
            'is_active', 'is_anonymous',
            'can_pledge', 'can_do_bank_transfer'
        )


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
            MemberPlatformSettings.load().display_member_names == 'first_name'
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
    homepage = PermissionField('home-detail')
    review_activities = UserPermissionField('activities.api_review_activity')

    class Meta(object):
        fields = [
            'project_list',
            'project_manage_list',
            'homepage',
            'review_activities'
        ]


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
    email = serializers.CharField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)

    full_name = serializers.CharField(source='get_full_name', read_only=True)
    short_name = serializers.CharField(source='get_short_name', read_only=True)
    can_pledge = serializers.BooleanField(read_only=True)
    can_do_bank_transfer = serializers.BooleanField(read_only=True)

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
            'id', 'email', 'full_name', 'short_name', 'initials',
            'primary_language', 'about_me', 'location', 'avatar', 'date_joined',
            'is_active', 'website', 'twitter', 'facebook',
            'skypename', 'skill_ids', 'favourite_theme_ids',
            'subscribed', 'segments', 'can_pledge', 'can_do_bank_transfer',
            'translate_user_content',
        )


class UserActivitySerializer(ModelSerializer):
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

    class JSONAPIMeta:
        resource_name = 'users/activities'


class ManageProfileSerializer(UserProfileSerializer):
    """
    Serializer for the member's private profile.
    """
    partial = True
    from_facebook = serializers.SerializerMethodField()
    place = OldPlaceSerializer(required=False, allow_null=True)

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
            'full_name', 'short_name', 'initials',
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
    accepted = serializers.BooleanField(read_only=True)
    access_code = serializers.CharField(required=False)

    def create(self, validated_data):
        password_authentication = PasswordAuthentication.load()
        email = validated_data.get('email', '')
        email_domain = email.split('@')[-1]
        accepted = True
        if (
            password_authentication.account_creation_rules == 'whitelist'
            and email_domain not in (password_authentication.email_domains or [])
        ):
            accepted = False
        (instance, _) = BB_USER_MODEL.objects.get_or_create(
            email__iexact=validated_data['email'],
            defaults={
                'is_active': False,
                'accepted': accepted,
                'email': validated_data['email']
            }
        )
        return instance

    class Meta(object):
        model = BB_USER_MODEL
        fields = ('id', 'email', 'url', 'segment_id', 'accepted', 'access_code')

    def validate_email(self, email):
        member = Member.objects.filter(email__iexact=email).first()
        if member:
            if member.is_active:
                raise serializers.ValidationError(
                    'A member with this email address already exists.',
                    code='email_in_use',
                )
        return email

    def validate(self, attrs):
        email = attrs.get('email', '')
        access_code = attrs.get('access_code', '')
        password_authentication = PasswordAuthentication.load()
        if not password_authentication:
            raise serializers.ValidationError(
                _('Signing up with email and password is not enabled.'),
                code='password_authentication_disabled'
            )

        email_domain = email.split('@')[1]
        email_domains = password_authentication.email_domains or []

        if (
            password_authentication.account_creation_rules in ['whitelist', 'whitelist_and_request']
            and len(email_domains)
            and email_domain not in email_domains
        ):
            if password_authentication.account_creation_rules == 'whitelist_and_request':
                if access_code:
                    if password_authentication.request_access_code != access_code:
                        raise serializers.ValidationError(
                            _('The access link you supplied is invalid. '
                              'Please contact us to request a new access link.'),
                            code='invalid_access_code'
                        )
                else:
                    raise serializers.ValidationError(
                        _('This email is not whitelisted, please contact us to request access.'),
                        code='request_access'
                    )
            else:
                raise serializers.ValidationError(
                    _('Only emails for specified domains are allowed. Please use your work e-mail address.'),
                    code='non_whitelisted_domain'
                )

        return attrs

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
        fields = ('id', 'password', 'token', 'jwt_token', 'first_name', 'last_name',)

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
    message = _('A user with this email address already exists')

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
        settings = MemberPlatformSettings.load()
        if not PasswordAuthentication.is_enabled():
            raise serializers.ValidationError(
                {'email': _('Signing up with email and password is not enabled.')}
            )

        if PasswordAuthentication.confirm_signup_enabled():
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
        fields = ('id', 'first_name', 'last_name', 'email', 'password', 'token',)

    class JSONAPIMeta:
        resource_name = 'auth/signup'


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


class MemberProfileSerializer(ModelSerializer):
    email = serializers.CharField(read_only=True)
    segments = ResourceRelatedField(
        many=True,
        queryset=Segment.objects.all(),
    )
    themes = ResourceRelatedField(
        many=True,
        queryset=Theme.objects.all(),
        source='favourite_themes'
    )

    skills = ResourceRelatedField(
        many=True,
        queryset=Skill.objects.all(),
    )
    remote_id = serializers.CharField(read_only=True)
    avatar = ImageField(required=False, allow_null=True)
    has_usable_password = serializers.BooleanField(read_only=True)

    class Meta():
        model = Member
        fields = (
            'id', 'first_name', 'last_name', 'about_me', 'full_name', 'required',
            'birthdate', 'segments', 'phone_number',
            'location', 'place', 'themes', 'skills', 'email',
            'search_distance', 'any_search_distance', 'exclude_online',
            'matching_options_set', 'remote_id', 'avatar',
            'subscribed', 'receive_reminder_emails', 'campaign_notifications',
            'has_usable_password', 'avatar', 'gender', 'translate_user_content',
            'terms_accepted'
        )

    class JSONAPIMeta():
        resource_name = 'member/profile'
        included_resources = [
            'location', 'location.subregion', 'location.subregion.region',
            'place.country', 'place', 'segments', 'avatar'
        ]

    included_serializers = {
        'place': 'bluebottle.geo.serializers.PlaceSerializer',
        'place.country': 'bluebottle.geo.serializers.InitiativeCountrySerializer',
        'location': 'bluebottle.geo.serializers.OfficeSerializer',
        'location.subregion': 'bluebottle.offices.serializers.SubregionSerializer',
        'location.subregion.region': 'bluebottle.offices.serializers.RegionSerializer',

        'segments': 'bluebottle.segments.serializers.SegmentListSerializer',
        'avatar': 'bluebottle.initiatives.serializers.AvatarImageSerializer',
    }

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


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, max_length=254)
    password = PasswordField(required=True, max_length=254)
    jwt_token = serializers.CharField(read_only=True)

    class Meta(object):
        fields = ('token', 'jwt_token', 'password')

    class JSONAPIMeta(object):
        resource_name = 'reset-token-confirmations'


class ValidatePassword:
    requires_context = True

    def __call__(self, value, field):
        if not field.context['request'].user.check_password(value):
            raise serializers.ValidationError(_('Password does not match'))


class PasswordProtectedMemberSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, max_length=128, validators=[ValidatePassword()]
    )
    jwt_token = serializers.CharField(source='get_jwt_token', read_only=True)

    class Meta(object):
        model = BB_USER_MODEL
        fields = ('password', 'jwt_token')


class EmailSetSerializer(PasswordProtectedMemberSerializer):
    email = serializers.EmailField(
        max_length=254,
        validators=[
            UniqueEmailValidator(
                queryset=BB_USER_MODEL.objects.all(), lookup='iexact'
            )
        ]
    )

    class Meta(PasswordProtectedMemberSerializer.Meta):
        fields = ('email',) + PasswordProtectedMemberSerializer.Meta.fields

    class JSONAPIMeta:
        resource_name = 'profile-email'

    def save(self):
        user = self.context['request'].user
        user.email = self.validated_data['email']
        user.save()


class PasswordUpdateSerializer(PasswordProtectedMemberSerializer):
    new_password = PasswordField(
        write_only=True, required=True, max_length=128)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs['password'] = attrs.pop('new_password')

        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()

        return instance

    class Meta(PasswordProtectedMemberSerializer.Meta):
        fields = ('new_password',) + PasswordProtectedMemberSerializer.Meta.fields

    class JSONAPIMeta:
        resource_name = 'profile-password'


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


class MemberPlatformSettingsSerializer(serializers.ModelSerializer):
    background = SorlImageField('1408x1080', crop='center')
    read_only_fields = serializers.SerializerMethodField()
    reminder_emails_enabled = serializers.SerializerMethodField()

    def get_read_only_fields(self, obj):
        try:
            return properties.TOKEN_AUTH['assertion_mapping'].keys()
        except (AttributeError, IndexError):
            return []

    def get_reminder_emails_enabled(self, obj):
        return any([obj.reminder_q1, obj.reminder_q2, obj.reminder_q3, obj.reminder_q4])

    class Meta(object):
        model = MemberPlatformSettings
        fields = (
            'consent_link',
            'disable_cookie_consent',
            'gtm_code',
            'closed',
            'session_only',
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
            'reminder_emails_enabled',
            'fiscal_month_offset',
            'fiscal_year',
            'fiscal_year_start',
            'fiscal_year_end',
            'retention_anonymize',
            'retention_delete',
            'read_only_fields',
            'translate_user_content',
            'explicit_terms'
        )


class CaptchaSerializer(serializers.Serializer):
    token = CaptchaField(required=True)
    id = serializers.SerializerMethodField()

    def get_id(self, obj):
        return str(uuid.uuid4())

    class Meta(object):
        fields = ('id', 'token')

    class JSONAPIMeta:
        resource_name = 'captcha-tokens'


class BaseAuthenticationMethodSerializer(ModelSerializer):
    """
    Base serializer for authentication methods.

    Only expose fields that are safe for anonymous users (the login page needs them).
    Secrets (OAuth client secrets, SAML attribute mappings, etc.) are never exposed.
    """
    class Meta:
        model = AuthenticationMethod
        fields = ('id', )


class PasswordAuthenticationSerializer(BaseAuthenticationMethodSerializer):
    request_access_instructions = serializers.CharField(read_only=True)

    class Meta(BaseAuthenticationMethodSerializer.Meta):
        model = PasswordAuthentication
        fields = BaseAuthenticationMethodSerializer.Meta.fields + (
            'confirm_signup',
            'account_creation_rules',
            'email_domains',
            'request_access_method',
            'request_access_instructions',
        )

    class JSONAPIMeta:
        resource_name = 'authentication-methods/password'


class FacebookAuthenticationSerializer(BaseAuthenticationMethodSerializer):
    class Meta(BaseAuthenticationMethodSerializer.Meta):
        model = FacebookAuthentication
        fields = BaseAuthenticationMethodSerializer.Meta.fields + ('client_id', )

    class JSONAPIMeta:
        resource_name = 'authentication-methods/facebook'


class GoogleAuthenticationSerializer(BaseAuthenticationMethodSerializer):
    class Meta(BaseAuthenticationMethodSerializer.Meta):
        model = GoogleAuthentication
        fields = BaseAuthenticationMethodSerializer.Meta.fields + ('client_id', )

    class JSONAPIMeta:
        resource_name = 'authentication-methods/google'


class SAMLAuthenticationSerializer(BaseAuthenticationMethodSerializer):
    class Meta(BaseAuthenticationMethodSerializer.Meta):
        model = SAMLAuthentication
        fields = BaseAuthenticationMethodSerializer.Meta.fields + (
            'entity_id',
            'single_sign_on_url',
            'admin_login_enabled',
            'organization'
        )

    class JSONAPIMeta:
        resource_name = 'authentication-methods/saml'
        included_resources = ['organization']

    included_serializers = {
        'organization': 'bluebottle.organizations.serializers.OrganizationSerializer',
    }


class AuthenticationMethodSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        PasswordAuthenticationSerializer,
        FacebookAuthenticationSerializer,
        GoogleAuthenticationSerializer,
        SAMLAuthenticationSerializer,
    ]

    class Meta:
        model = AuthenticationMethod
        fields = ('id', 'enabled')

    class JSONAPIMeta:
        resource_name = 'authentication-methods'
        included_resources = ['organization']

    included_serializers = {
        'organization': 'bluebottle.organizations.serializers.OrganizationSerializer',
    }
