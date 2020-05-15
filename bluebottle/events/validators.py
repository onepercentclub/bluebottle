from django.utils.translation import ugettext_lazy as _

from bluebottle.utils.models import Validator


class RegistrationDeadlineValidator(Validator):
    field = 'registration_deadline'
    code = 'registration-deadline'
    message = _('Registration deadline should be before the start time'),

    def is_valid(self):
        return (
            not self.instance.registration_deadline or (
                self.instance.start and
                self.instance.registration_deadline < self.instance.start.date()
            )
        )
