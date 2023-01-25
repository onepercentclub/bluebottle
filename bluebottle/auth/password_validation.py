from gettext import ngettext

from django.contrib.auth.password_validation import MinimumLengthValidator
from django.core.exceptions import ValidationError


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
