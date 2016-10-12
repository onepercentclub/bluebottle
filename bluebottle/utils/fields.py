from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.conf import settings
from django.utils.functional import lazy
from django.utils.translation import ugettext as _

import sorl.thumbnail
from djmoney.models.fields import MoneyField as DjangoMoneyField

from bluebottle.clients import properties


def get_currency_choices():
    return [(currency['code'], currency['name']) for currency in properties.CURRENCIES_ENABLED]


def get_default_currency():
    return properties.CURRENCIES_ENABLED[0]['code']


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
