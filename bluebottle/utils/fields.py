import json
import mimetypes
import xml.etree.cElementTree as et
from builtins import object
from builtins import str

import inflection
import sorl.thumbnail
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import gettext as _
from djmoney.forms import MoneyField as MoneyFormField
from djmoney.models.fields import MoneyField as DjangoMoneyField
from rest_framework import serializers
from rest_framework.fields import Field
from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField,
    MANY_RELATION_KWARGS,
    LINKS_PARAMS
)

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

    def get_default_currency(self):
        from bluebottle.funding.models import PaymentProvider
        return PaymentProvider.get_default_currency()

    def get_currency_choices(self):
        from bluebottle.funding.models import PaymentProvider
        return PaymentProvider.get_currency_choices()

    def deconstruct(self):
        name, path, args, kwargs = super(MoneyField, self).deconstruct()

        if self.default is not None:
            kwargs['default'] = self.default.amount
        if self.default_currency != self.get_default_currency():
            kwargs['default_currency'] = str(self.default_currency)
        if self.currency_choices != self.get_currency_choices():
            kwargs['currency_choices'] = self.currency_choices
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        # For the form load the actual available currencies from PaymentProviders
        defaults = {'form_class': MoneyFormField}
        defaults.update(kwargs)
        self.default_currency = self.get_default_currency()
        self.currency_choices = self.get_currency_choices()
        return super(MoneyField, self).formfield(**kwargs)


class LegacyMoneyField(MoneyField):

    def get_default_currency(self):
        return 'EUR'

    def get_currency_choices(self):
        return [('EUR', 'Euro')]


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


class RichTextField(serializers.CharField):
    def to_representation(self, value):
        return clean_html(super().to_representation(value.html))

    def to_internal_value(self, data):
        return json.dumps({'html': super().to_internal_value(data), 'delta': ''})


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
        return str(clean_html(data))


class PrivateFileField(models.FileField):

    def __init__(self, verbose_name=None, name=None, upload_to='', storage=None, **kwargs):
        # Check if upload_to already has private path
        # This fixes loops and randomly added migrations
        if not upload_to.startswith(b'private'):
            upload_to = 'private/{}'.format(upload_to)
        super(PrivateFileField, self).__init__(
            verbose_name=verbose_name, name=name, upload_to=upload_to, storage=storage, **kwargs
        )


class FSMStatusValidator(object):
    requires_context = True

    def __call__(self, value, serializer_field):
        available_transitions = getattr(
            self.instance,
            'get_available_{}_transitions'.format(serializer_field.source)
        )()

        transitions = [
            transition for transition in available_transitions if
            transition.target == value and not transition.options.get('automatic')
        ]

        if len(transitions) != 1:
            raise ValidationError(
                'Cannot transition from {} to {}'.format(
                    getattr(serializer_field.instance, serializer_field.source),
                    value
                )
            )


class FSMField(serializers.CharField):
    def __init__(self, **kwargs):
        super(FSMField, self).__init__(**kwargs)
        validator = FSMStatusValidator()
        self.validators.append(validator)


class ValidationErrorsField(serializers.ReadOnlyField):
    def __init__(self, ignore=None, *args, **kwargs):
        self.ignore = ignore or []
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        return [
            {
                "title": str(error),
                "code": error.code,
                "source": {
                    "pointer": "/data/attributes/{}".format(
                        inflection.dasherize(error.field).replace(".", "/")
                    )
                },
            }
            for error in value
            if error.code not in self.ignore
        ]


class RequiredErrorsField(serializers.ReadOnlyField):
    def to_representation(self, value):
        return [
            {
                'title': _('This field is required'),
                'code': 'required',
                'source': {
                    'pointer': '/data/attributes/{}'.format(inflection.dasherize(field).replace('.', '/'))
                }
            } for field in value
        ]


class PolymorhpicSerializerMethodFieldBase(Field):
    def __init__(self, serializer_class, method_name=None, *args, **kwargs):
        self.method_name = method_name
        kwargs["source"] = "*"
        kwargs["read_only"] = True
        super().__init__(serializer_class, **kwargs)

    def bind(self, field_name, parent):
        default_method_name = "get_{field_name}".format(field_name=field_name)
        if self.method_name is None:
            self.method_name = default_method_name
        super().bind(field_name, parent)

    def get_attribute(self, instance):
        serializer_method = getattr(self.parent, self.method_name)
        return serializer_method(instance)


class PolymorphicManySerializerMethodResourceRelatedField(
    PolymorhpicSerializerMethodFieldBase, PolymorphicResourceRelatedField
):
    def __init__(self, polymorphic_serializer, child_relation=None, **kwargs):
        assert child_relation is not None, "`child_relation` is a required argument."
        self.child_relation = child_relation
        super().__init__(polymorphic_serializer, **kwargs)
        # self.child_relation.bind(field_name="", parent=self)

    def to_representation(self, value):
        serializers = [
            self.polymorphic_serializer(item).to_representation(item) for item in value
        ]

        return [
            {'type': serializer['type'], 'id': force_str(serializer['id'])}
            for serializer in serializers
        ]


class PolymorphicSerializerMethodResourceRelatedField(
    PolymorhpicSerializerMethodFieldBase, PolymorphicResourceRelatedField
):
    """
    Allows us to use serializer method RelatedFields
    with return querysets
    """

    many_kwargs = [
        *MANY_RELATION_KWARGS, *LINKS_PARAMS, "method_name", "model",
    ]
    many_cls = PolymorphicManySerializerMethodResourceRelatedField

    @classmethod
    def many_init(cls, *args, **kwargs):
        list_kwargs = {"child_relation": cls(*args, **kwargs)}
        for key in kwargs:
            if key in cls.many_kwargs:
                list_kwargs[key] = kwargs[key]
        return cls.many_cls(*args, **list_kwargs)
