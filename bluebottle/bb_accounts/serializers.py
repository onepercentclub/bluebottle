from django.conf import settings
from django import forms
from django.contrib.auth import get_user_model

from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import (
    SorlImageField, ImageSerializer, TaggableSerializerMixin)
from bluebottle.geo.models import Country
from bluebottle.utils.serializers import URLField
from bluebottle.utils.validators import validate_postal_code


BB_USER_MODEL = get_user_model()


class UserPreviewSerializer(serializers.ModelSerializer):
    """
    Serializer for a subset of a member's public profile. This is usually embedded into other serializers.
    """
    def __init__(self, *args, **kwargs):
        kwargs['read_only'] = True
        super(UserPreviewSerializer, self).__init__(*args, **kwargs)

    avatar = SorlImageField('picture', '133x133', crop='center', colorspace="GRAY")

    # TODO: Remove first/last name and only use these
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    short_name = serializers.CharField(source='get_short_name', read_only=True)

    class Meta:
        model = BB_USER_MODEL
        fields = ('id', 'first_name', 'last_name', 'username', 'avatar', 'full_name', 'short_name')


class CurrentUserSerializer(UserPreviewSerializer):
    """
    Serializer for the current authenticated user. This is the same as the serializer for the member preview with the
    addition of id_for_ember.
    """
    # This is a hack to work around an issue with Ember-Data keeping the id as 'current'.
    id_for_ember = serializers.IntegerField(source='id', read_only=True)
    full_name = serializers.Field(source='get_full_name')

    class Meta:
        model = BB_USER_MODEL
        fields = UserPreviewSerializer.Meta.fields + ('id_for_ember', 'primary_language', 'email', 'full_name')


class UserProfileSerializer(TaggableSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for a member's public profile.
    """
    url = serializers.HyperlinkedIdentityField(view_name='user-profile-detail')
    picture = ImageSerializer(required=False)
    date_joined = serializers.DateTimeField(read_only=True)
    username = serializers.CharField(read_only=True)

    website = URLField(required=False)
    #tags = TagSerializer()

    # TODO: Remove first/last name and only use these
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    short_name = serializers.CharField(source='get_short_name', read_only=True)

    class Meta:
        model = BB_USER_MODEL
        fields = ('id', 'url', 'username', 'first_name', 'last_name', 'full_name', 'short_name', 'picture',
                  'about', 'why', 'website', 'availability', 'date_joined', 'location', 'twitter', 'facebook',
                  'skypename')


# Thanks to Neamar Tucote for this code:
# https://groups.google.com/d/msg/django-rest-framework/abMsDCYbBRg/d2orqUUdTqsJ
class PasswordField(serializers.CharField):
    """ Special field to update a password field. """
    widget = forms.widgets.PasswordInput
    hidden_password_string = '********'

    def from_native(self, value):
        """ Hash if new value sent, else retrieve current password. """
        from django.contrib.auth.hashers import make_password
        if value == self.hidden_password_string or value == '':
            return self.parent.object.password
        else:
            return make_password(value)

    def to_native(self, value):
        """ Hide hashed-password in API display. """
        return self.hidden_password_string


class UserSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing and editing a user's settings. This should only be accessible to authenticated users.
    """
    # FIXME: We should really be serializing 'birthdate' as a DateField but that would require some additional work
    #        in our ember-data adapter. This could cause birthdate's to not be savable in some cases.
    birthdate = serializers.DateTimeField(required=False)
    email = serializers.EmailField(required=False)
    primary_language = serializers.ChoiceField(choices=settings.LANGUAGES, default='en', required=False)

    # Address
    line1 = serializers.CharField(source='address.line1', max_length=100, required=False)
    line2 = serializers.CharField(source='address.line2', max_length=100, required=False)
    city = serializers.CharField(source='address.city', max_length=100, required=False)
    state = serializers.CharField(source='address.state', max_length=100, required=False)
    country = serializers.CharField(source='address.country.alpha2_code', required=False)
    postal_code = serializers.CharField(source='address.postal_code', max_length=20, required=False)

    def validate_postal_code(self, attrs, source):
        if source in attrs:
            value = attrs[source]
            country_code = ''
            if 'address.country.alpha2_code' in attrs:
                country_code = attrs['address.country.alpha2_code']
            elif self.object and self.object.address and self.object.address.country:
                country_code = self.object.address.country.alpha2_code

            if country_code:
                validate_postal_code(value, country_code)
        return attrs

    class Meta:
        model = BB_USER_MODEL
        # TODO: Add * password update using password field.
        #           * Facebook connect
        fields = ('id', 'email', 'share_time_knowledge', 'share_money', 'newsletter', 'gender', 'birthdate',
                  'user_type', 'line1', 'line2', 'city', 'state', 'postal_code', 'country', 'primary_language')

    def restore_object(self, attrs, instance=None):
        """ Overridden to enable address write."""
        instance = super(UserSettingsSerializer, self).restore_object(attrs, instance)

        address_fields = dict((key.replace('address.', ''), val) for key, val in attrs.items() if key.startswith('address.'))
        address = instance.address
        if address is not None:
            for key, val in address_fields.items():
                if key == 'country.alpha2_code':
                    if val:
                        address.country = Country.objects.get(alpha2_code=val)
                else:
                    setattr(address, key, val)
            address.save()

        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating users. This can only be used for creating users (POST) and should not be used for listing,
    editing or viewing users.
    """
    email = serializers.EmailField(required=True, max_length=254)
    password = PasswordField(required=True, max_length=128)
    username = serializers.CharField(read_only=True)

    class Meta:
        model = BB_USER_MODEL
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'password')


class PasswordResetSerializer(serializers.Serializer):
    """
    Password reset request serializer that uses the email validation from the Django PasswordResetForm.
    """
    email = serializers.EmailField(required=True, max_length=254)

    class Meta:
        fields = ('email',)

    def __init__(self, password_reset_form=None, *args, **kwargs):
        self.password_reset_form = password_reset_form
        super(PasswordResetSerializer, self).__init__(*args, **kwargs)

    def validate_email(self, attrs, source):
        if attrs is not None:  # Don't need this check in newer versions of DRF2.
            value = attrs[source]
            self.password_reset_form.cleaned_data = {"email": value}
            return self.password_reset_form.clean_email()


class PasswordSetSerializer(serializers.Serializer):
    """
    A serializer that lets a user change set his/her password without entering the old password. This uses the
    validation from the Django SetPasswordForm.
    """
    # We can't use the PasswordField here because it hashes the passwords with a salt which means we can't compare the
    # two passwords to see if they are the same.
    new_password1 = serializers.CharField(required=True, max_length=128, widget=forms.widgets.PasswordInput)
    new_password2 = serializers.CharField(required=True, max_length=128, widget=forms.widgets.PasswordInput)

    class Meta:
        fields = ('new_password1', 'new_password2')

    def __init__(self, password_set_form=None, *args, **kwargs):
        self.password_set_form = password_set_form
        super(PasswordSetSerializer, self).__init__(*args, **kwargs)

    def validate_new_password2(self, attrs, source):
        if attrs is not None:  # Don't need this check in newer versions of DRF2.
            value = attrs[source]
            self.password_set_form.cleaned_data = {"new_password1": attrs['new_password1'], "new_password2": value}
            return self.password_set_form.clean_new_password2()
