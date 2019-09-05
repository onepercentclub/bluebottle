import mimetypes
import xml.etree.cElementTree as et

import sorl.thumbnail
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext as _
from djmoney.forms import MoneyField as MoneyFormField
from djmoney.models.fields import MoneyField as DjangoMoneyField
from rest_framework import serializers

from .utils import clean_html


class MoneyField(DjangoMoneyField):
    def __init__(self, verbose_name=None, name=None,
                 max_digits=12, decimal_places=2, default=None,
                 default_currency=None,
                 currency_choices=None,
                 **kwargs):
        default_currency = 'EUR'
        currency_choices = [('EUR', 'Euro')]
        super(MoneyField, self).__init__(
            verbose_name=verbose_name, name=name,
            max_digits=max_digits, decimal_places=decimal_places, default=default,
            default_currency=default_currency,
            currency_choices=currency_choices,
            **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(MoneyField, self).deconstruct()
        from bluebottle.funding.models import PaymentProvider

        if self.default is not None:
            kwargs['default'] = self.default.amount
        if self.default_currency != PaymentProvider.get_default_currency():
            kwargs['default_currency'] = str(self.default_currency)
        if self.currency_choices != PaymentProvider.get_currency_choices():
            kwargs['currency_choices'] = self.currency_choices
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        from bluebottle.funding.models import PaymentProvider
        # For the form load the actual available currencies from PaymentProviders
        defaults = {'form_class': MoneyFormField}
        defaults.update(kwargs)
        self.currency_choices = PaymentProvider.get_currency_choices()
        self.default_currency = PaymentProvider.get_default_currency()
        return super(MoneyField, self).formfield(**kwargs)


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

        If the item cannot be converted to an image, check if the file is and svg
        """
        if data and data.content_type not in settings.IMAGE_ALLOWED_MIME_TYPES:
            raise forms.ValidationError(self.error_messages['invalid_image'])

        if hasattr(data, 'name') and mimetypes.guess_type(data.name)[0] not in settings.IMAGE_ALLOWED_MIME_TYPES:
            raise forms.ValidationError(self.error_messages['invalid_image'])

        try:
            return super(RestrictedImageFormField, self).to_python(data)
        except ValidationError:
            test_file = super(sorl.thumbnail.fields.ImageFormField, self).to_python(data)

            if self.is_svg(test_file):
                return test_file
            else:
                raise

    def is_svg(self, f):
        """
        Check if provided file is svg
        """
        f.seek(0)
        tag = None
        try:
            for event, el in et.iterparse(f, ('start',)):
                tag = el.tag
                break
        except et.ParseError:
            pass
        return tag == '{http://www.w3.org/2000/svg}svg'


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

    def __init__(self, verbose_name=None, name=None, upload_to='', storage=None, **kwargs):
        # Check if upload_to already has private path
        # This fixes loops and randomly added migrations
        if not upload_to.startswith('private'):
            upload_to = 'private/{}'.format(upload_to)
        super(PrivateFileField, self).__init__(
            verbose_name=verbose_name, name=name, upload_to=upload_to, storage=storage, **kwargs
        )


class FSMStatusValidator(object):
    def set_context(self, serializers_field):
        self.instance = serializers_field.parent.instance
        self.source = serializers_field.source

    def __call__(self, value):
        available_transitions = getattr(
            self.instance,
            'get_available_{}_transitions'.format(self.source)
        )()

        transitions = [
            transition for transition in available_transitions if
            transition.target == value
        ]

        if len(transitions) != 1:
            raise ValidationError(
                'Cannot transition from {} to {}'.format(
                    getattr(self.instance, self.source),
                    value
                )
            )


class FSMField(serializers.CharField):
    def __init__(self, **kwargs):
        super(FSMField, self).__init__(**kwargs)
        validator = FSMStatusValidator()
        self.validators.append(validator)
