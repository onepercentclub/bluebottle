import re
from django.utils.translation import ngettext, get_language
from django.utils.translation import gettext as _

from difflib import SequenceMatcher
from django.contrib.auth.password_validation import (
    MinimumLengthValidator,
    CommonPasswordValidator as BaseCommonPasswordValidator,
    UserAttributeSimilarityValidator as BaseUserAttributeSimilarityValidator
)

from django.core.exceptions import (
    FieldDoesNotExist, ValidationError,
)


class CustomMinimumLengthValidator(MinimumLengthValidator):
    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                ngettext(
                    "Password should at least be %(min_length)d character.",
                    "Password should at least be %(min_length)d characters.",
                    self.min_length
                ),
                code='password_too_short',
                params={'min_length': self.min_length},
            )


class CommonPasswordValidator(BaseCommonPasswordValidator):
    def validate(self, password, user=None):
        if password.lower().strip() in self.passwords:
            raise ValidationError(
                _("This password is too common, be adventurous!"),
                code='password_too_common',
            )


class UserAttributeSimilarityValidator(BaseUserAttributeSimilarityValidator):
    def validate(self, password, user=None):
        if not user:
            return

        for attribute_name in self.user_attributes:
            value = getattr(user, attribute_name, None)
            if not value or not isinstance(value, str):
                continue
            value_parts = re.split(r'\W+', value) + [value]
            for value_part in value_parts:
                if SequenceMatcher(a=password.lower(), b=value_part.lower()).quick_ratio() >= self.max_similarity:
                    try:
                        verbose_name = str(user._meta.get_field(attribute_name).verbose_name)
                    except FieldDoesNotExist:
                        verbose_name = attribute_name
                    raise ValidationError(
                        _("The password is too similar to your %(verbose_name)s, think outside the box!"),
                        code='password_too_similar',
                        params={'verbose_name': verbose_name},
                    )
