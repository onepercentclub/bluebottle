from babel.numbers import get_currency_name


from rest_framework import serializers

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.core.urlresolvers import resolve, reverse
from django.db import models
from django.conf import settings
from django.utils.functional import lazy
from django.utils.translation import ugettext as _

import sorl.thumbnail
from djmoney.models.fields import MoneyField as DjangoMoneyField

from bluebottle.clients import properties

from .utils import clean_html


def get_currency_choices():
    currencies = []
    for method in properties.PAYMENT_METHODS:
        currencies += method['currencies'].keys()

    return [(currency, get_currency_name(currency)) for currency in set(currencies)]


def get_default_currency():
    return getattr(properties, 'DEFAULT_CURRENCY')


class MoneyField(DjangoMoneyField):
    def __init__(self, verbose_name=None, name=None,
                 max_digits=12, decimal_places=2, default=None,
                 default_currency=lazy(get_default_currency, str)(),
                 currency_choices=lazy(get_currency_choices, tuple)(),
                 **kwargs):
        super(MoneyField, self).__init__(
            verbose_name=verbose_name, name=name,
            max_digits=max_digits, decimal_places=decimal_places, default=default,
            default_currency=default_currency,
            currency_choices=currency_choices,
            **kwargs)


# Validation references:
# http://www.mobilefish.com/services/elfproef/elfproef.php
# http://www.credit-card.be/BankAccount/ValidationRules.htm#NL_Validation
class DutchBankAccountFieldValidator(RegexValidator):
    main_message = _("Dutch bank account numbers have 1 - 7, 9 or 10 digits.")

    def __init__(self, regex=None, message=None, code=None):
        super(DutchBankAccountFieldValidator, self).__init__(regex='^[0-9]+$',
                                                             message=self.main_message)

    def __call__(self, value):
        super(DutchBankAccountFieldValidator, self).__call__(value)
        if len(value) != 9 and len(value) != 10 and not 1 <= len(value) <= 7:
            raise ValidationError(self.main_message)

        # Perform the eleven test validation on non-PostBank numbers.
        if len(value) == 9 or len(value) == 10:
            if len(value) == 9:
                value = "0" + value

            eleven_test_sum = sum(
                [int(a) * b for a, b in zip(value, range(1, 11))])
            if eleven_test_sum % 11 != 0:
                raise ValidationError(_("Invalid Dutch bank account number."))


class DutchBankAccountField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 10)
        super(DutchBankAccountField, self).__init__(*args, **kwargs)
        self.validators.append(DutchBankAccountFieldValidator())


class ImageField(sorl.thumbnail.fields.ImageField):
    """ Image field that only allow certain mime-types.

    Overriden from sorl.thumbnail.fields.ImageField.

    The list of valid mime-types can be set using the IMAGE_ALLOWED_MIME_TYPES setting.
    """

    def formfield(self, **kwargs):
        defaults = {'form_class': RestrictedImageFormField}
        defaults.update(kwargs)
        return super(ImageField, self).formfield(**defaults)


class RestrictedImageFormField(sorl.thumbnail.fields.ImageFormField):
    """ Actual FormField that does the validation of the mime-types."""

    def to_python(self, data):
        """
        Checks that the file-upload field data contains a valid image (GIF,
        JPG, PNG, possibly others -- whatever the engine supports).
        """
        if data and data.content_type not in settings.IMAGE_ALLOWED_MIME_TYPES:
            raise forms.ValidationError(self.error_messages['invalid_image'])
        return super(RestrictedImageFormField, self).to_python(data)


# If south is installed, ensure that DutchBankAccountField will be introspected just like a normal CharField
try:
    from south.modelsinspector import add_introspection_rules

    add_introspection_rules([], ["^apps.fund\.fields\.DutchBankAccountField"])
except ImportError:
    pass


class SafeField(serializers.CharField):
    def to_representation(self, value):
        """ Reading / Loading the story field """
        return clean_html(value)

    def to_internal_value(self, data):
        """
        Saving the story text

        Convert &gt; and &lt; back to HTML tags so Beautiful Soup can clean
        unwanted tags. Script tags are sent by redactor as
        "&lt;;script&gt;;", Iframe tags have just one semicolon.
        """
        data = data.replace("&lt;;", "<").replace("&gt;;", ">")
        data = data.replace("&lt;", "<").replace("&gt;", ">")
        return unicode(clean_html(data))


class PrivateFileField(models.FileField):
    def __init__(self, upload_to='', *args, **kwargs):
        super(PrivateFileField, self).__init__(
            upload_to='private/' + upload_to, *args, **kwargs
        )


class PermissionField(serializers.Field):
    """
    Field that can be used to return permission of the current and related view.

    `view_name`: The name of the view
    `view_args`: A list of attributes that are passed into the url for the view
    """
    def __init__(self, view_name, view_args=None, *args, **kwargs):
        self.view_name = view_name
        self.view_args = view_args or []

        kwargs['read_only'] = True

        super(PermissionField, self).__init__(*args, **kwargs)

    def get_attribute(self, obj):
        return obj  # Just pass the whole object back

    def to_representation(self, value):
        """
        Returns an dict with the permissions the current user has on the view and parent:
        {
            "PATCH": True,
            "GET": True,
            "DELETE": False
        }
        """
        # Instantiate the view
        args = [getattr(value, arg) for arg in self.view_args]
        view_func = resolve(reverse(self.view_name, args=args)).func
        view = view_func.view_class(**view_func.view_initkwargs)

        # Loop over all methods and check the permissions on the view
        permissions = {}
        for method in view.allowed_methods:
            permissions[method] = all(
                perm.check_object_permission(
                    method, self.context['request'].user, view, value
                ) for perm in view.get_permissions()
            )

        return permissions


