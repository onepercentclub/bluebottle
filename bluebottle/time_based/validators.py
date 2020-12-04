from django.utils.translation import ugettext_lazy as _

from bluebottle.utils.models import Validator


class RegistrationDeadlineValidator(Validator):
    field = 'registration_deadline'
    code = 'registration-deadline'
    message = _('Registration deadline should be before the start or end date')

    def is_valid(self):
        return (
            not self.instance.registration_deadline or (
                self.maxDate and
                self.instance.registration_deadline < self.maxDate
            )
        )


class DateActivityRegistrationDeadlineValidator(RegistrationDeadlineValidator):
    @property
    def maxDate(self):
        return self.instance.start.date()


class PeriodActivityRegistrationDeadlineValidator(RegistrationDeadlineValidator):
    @property
    def maxDate(self):
        return self.instance.start or self.instance.deadline
