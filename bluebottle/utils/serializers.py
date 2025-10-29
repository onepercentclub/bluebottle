from future import standard_library
standard_library.install_aliases()

from operator import attrgetter
from builtins import str
from builtins import object
import json
from html.parser import HTMLParser

from urllib.error import HTTPError
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.urls import resolve, reverse
from django.core.validators import BaseValidator
from django.http.request import validate_host
from django.utils.translation import gettext_lazy as _
from moneyed import Money
from rest_framework import serializers
from rest_framework.utils import model_meta

from rest_framework.relations import ManyRelatedField

from django_recaptcha import client

from bluebottle.utils.utils import get_client_ip, get_current_language
from bluebottle.utils.translations import translate_text_cached
from .models import Language, TranslationPlatformSettings


class MaxAmountValidator(BaseValidator):
    compare = lambda self, a, b: a.amount > b
    message = _('Ensure this value is less than or equal to %(limit_value)s.')
    code = 'max_amount'


class MinAmountValidator(BaseValidator):
    compare = lambda self, a, b: a.amount < b
    message = _('Ensure this value is greater than or equal to %(limit_value)s.')
    code = 'min_amount'


class MoneySerializer(serializers.DecimalField):
    default_error_messages = {
        'max_amount': _('Ensure this amount is less than or equal to {max_amount}.'),
        'min_amount': _('Ensure this amount is greater than or equal to {min_amount}.'),
    }

    def __init__(self, max_digits=12, decimal_places=2, max_amount=None, min_amount=None, **kwargs):
        super(MoneySerializer, self).__init__(
            max_digits=max_digits,
            decimal_places=decimal_places,
            **kwargs
        )
        if max_amount is not None:
            message = self.error_messages['max_amount'].format(max_amount=max_amount)
            self.validators.append(MaxAmountValidator(max_amount, message=message))

        if min_amount is not None:
            message = self.error_messages['min_amount'].format(min_amount=min_amount)
            self.validators.append(MinAmountValidator(min_amount, message=message))

    def to_representation(self, instance):
        return {
            'amount': instance.amount,
            'currency': str(instance.currency)
        }

    def to_internal_value(self, data):
        if not data:
            return data
        try:
            return Money(float(data), 'EUR')
        except ValueError:
            data = json.loads(data)
            return Money(data.get('amount', 0) or 0, data['currency'])
        except TypeError:
            return Money(data.get('amount', 0) or 0, data['currency'])


class LanguageSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source='full_code')

    class Meta(object):
        model = Language
        fields = ('id', 'code', 'language_name', 'native_name', 'default')


class MLStripper(HTMLParser):
    """ Used to strip HTML tags for meta fields (e.g. description) """

    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


class BasePermissionField(serializers.Field):
    """ Field that can be used to return permission of the current and related view.

    `view_name`: The name of the view
    `view_args`: A list of attributes that are passed into the url for the view
    """

    def __init__(self, view_name, view_args=None, *args, **kwargs):
        self.view_name = view_name
        self.view_args = view_args or []

        kwargs['read_only'] = True

        super(BasePermissionField, self).__init__(*args, **kwargs)

    def _get_view(self, value):
        args = [getattr(value, arg) for arg in self.view_args]
        view_func = resolve(reverse(self.view_name, args=args)).func
        return view_func.view_class(**view_func.view_initkwargs)

    def _method_permissions(self, method, user, view, value):
        message = '_method_permissions() must be implemented on {}'.format(self)
        raise NotImplementedError(message)

    def get_attribute(self, value):
        return value  # Just pass the whole object back

    def to_representation(self, value):
        """ Return a dict with the permissions the current user has on the view and parent.

        Example response:
        {
            "PATCH": True,
            "GET": True,
            "DELETE": False
        }
        """

        view = self._get_view(value)

        # Loop over all methods and check the permissions on the view
        permissions = {}
        user = self.context['request'].user

        for method in view.allowed_methods:
            permissions[method] = self._method_permissions(method, user, view, value)
        return permissions


class PermissionField(BasePermissionField):
    """
    Field that can be used to return permissions that are not directly related to the current view

    (E.g.) the permissions field on the current user object
    """
    def _method_permissions(self, method, user, view, value):
        return all(perm.has_action_permission(
            method, user, view.model
        ) for perm in view.get_permissions())


class ResourcePermissionField(BasePermissionField):
    """ Field that can be used to return permissions for a view with object. """

    def _method_permissions(self, method, user, view, value):
        for permission in view.get_permissions():
            if not (
                permission.has_object_action_permission(method, user, value)
                and permission.has_action_permission(method, user, view.model)
            ):
                return False

        if hasattr(view, "related_permission_classes"):
            for related, permissions in list(view.related_permission_classes.items()):
                related_obj = attrgetter(related)(value)
                for permission in permissions:
                    if not permission().has_object_action_permission(
                        method, user, related_obj
                    ):
                        return False

        return True


class RelatedResourcePermissionField(BasePermissionField):
    """ Field that can be used to return permission for a related view. """

    def _method_permissions(self, method, user, view, value):
        return all(
            (perm.has_parent_permission(method, user, value, view.model) and
             perm.has_action_permission(method, user, view.model))
            for perm in view.get_permissions())


class CaptchaField(serializers.CharField):
    def to_internal_value(self, data):
        result = super(CaptchaField, self).to_internal_value(data)

        try:
            captcha = client.submit(
                recaptcha_response=result,
                private_key=settings.RECAPTCHA_PRIVATE_KEY,
                remoteip=get_client_ip(self.context['request'])
            )
        except HTTPError:  # Catch timeouts, etc
            raise serializers.ValidationError(
                self.error_messages["captcha_error"],
                code="captcha_error"
            )

        if not captcha.is_valid or not validate_host(captcha.extra_data['hostname'], settings.ALLOWED_HOSTS):
            raise serializers.ValidationError('Captcha value is not valid')

        return result


class NoCommitMixin(object):
    def update(self, instance, validated_data):
        serializers.raise_errors_on_nested_writes('update', self, validated_data)
        info = model_meta.get_field_info(instance)

        # Simply set each attribute on the instance, and then save it.
        # Note that unlike `.create()` we don't need to treat many-to-many
        # relationships as being a special case. During updates we already
        # have an instance pk for the relationships to be associated with.
        for attr, value in list(validated_data.items()):
            if attr in info.relations and info.relations[attr].to_many:
                field = getattr(instance, attr)
                field.set(value)
            else:
                setattr(instance, attr, value)

        if not self.context['request'].META.get('HTTP_X_DO_NOT_COMMIT'):
            instance.save()

        return instance


class TruncatedCharField(serializers.CharField):
    def __init__(self, length, *args, **kwargs):
        self.length = length

        super(TruncatedCharField, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        return data[:self.length]


class TranslationPlatformSettingsSerializer(serializers.ModelSerializer):

    class Meta(object):
        model = TranslationPlatformSettings
        fields = '__all__'

    def get_fields(self):
        try:
            translation = self.instance.get_translation(self.instance.language_code)
        except self.instance.DoesNotExist:
            return {}

        result = dict(
            (field.verbose_name, serializers.CharField(max_length=100, source=field.name))
            for field in translation._meta.fields
            if isinstance(field, models.CharField) and field.name != 'language_code'
        )

        return result

    def to_representation(self, obj):
        return super(TranslationPlatformSettingsSerializer, self).to_representation(obj)


class ManyAnonymizedResourceRelatedField(ManyRelatedField):
    def get_attribute(self, parent):
        result = super().get_attribute(parent)

        if parent.anonymized:
            result = [AnonymousUser() for item in result.all()]

        return result


class TranslationsSerializer(serializers.Field):
    """
    A field that translates specified fields from an object to the current language.
    
    Usage:
        class MySerializer(serializers.ModelSerializer):
            translations = TranslationsSerializer(fields=['title', 'description'])
        
        # API response will include:
        # "translations": {"title": "Translated title", "description": "Translated description"}
    """
    
    def __init__(self, fields=None, **kwargs):
        self.translation_fields = fields or []
        kwargs['read_only'] = True
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        """Return the instance itself so we can access all fields in to_representation."""
        return instance

    def to_representation(self, instance):
        if not instance:
            return {}
        
        target_language = get_current_language()
        if not target_language:
            # If no target language available, return original values
            return {
                field: self._get_field_value(instance, field) 
                for field in self.translation_fields
            }
        
        source_language = self._get_source_language(instance)
        translated_data = {}
        
        for field_name in self.translation_fields:
            original_value = self._get_field_value(instance, field_name)
            
            if original_value:
                if hasattr(original_value, 'html'):
                    original_value = original_value.html
                text_value = str(original_value)
                translated_value = self._translate_field(
                    text_value, 
                    target_language, 
                    source_language
                )
                translated_data[field_name] = translated_value
            else:
                translated_data[field_name] = original_value
        
        return translated_data
    
    def _translate_field(self, text, target, source):
        """
        Translate a text field using the cached translation service.
        
        Args:
            text: The text to translate
            target: Target language code
            source: Source language code
            
        Returns:
            Translated text or original text if translation fails
        """
        if not text:
            return ""
        
        # If original already matches target language, return as-is
        if source and source.lower().startswith(target.lower()):
            return text
            
        try:
            return translate_text_cached(text=text, target_lang=target, source_lang=source)
        except Exception as e:
            # Fail-safe: fall back to original text, don't explode the API
            return text

    def _get_source_language(self, obj):
        """Get the source language from the object."""
        return getattr(obj, "language", "nl")
    
    def _get_field_value(self, obj, field_name):
        """
        Get the value of a field from the object, handling nested attributes and special cases.
        
        Args:
            obj: The object to get the field value from
            field_name: The name of the field to get
            
        Returns:
            The field value or None if not found
        """
        try:
            # Handle nested field access (e.g., 'description.html')
            if '.' in field_name:
                value = obj
                for attr in field_name.split('.'):
                    value = getattr(value, attr, None)
                    if value is None:
                        break
                return value
            else:
                return getattr(obj, field_name, None)
        except (AttributeError, TypeError):
            return None

