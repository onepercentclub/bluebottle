from django.db.models import Min
from django.utils.translation import gettext_lazy as _

from bluebottle.utils.models import Validator


class RegistrationDeadlineValidator(Validator):
    field = 'registration_deadline'
    code = 'registration-deadline'
    message = _('Registration deadline should be before the start or end date')

    def is_valid(self):
        return (
            not self.instance.registration_deadline or
            not self.maxDate or (
                self.maxDate and
                self.instance.registration_deadline < self.maxDate
            )
        )


class DateActivityRegistrationDeadlineValidator(RegistrationDeadlineValidator):
    @property
    def maxDate(self):
        if self.instance.slots.filter(start__isnull=False).count():
            return self.instance.slots.filter(start__isnull=False).aggregate(start=Min('start'))['start'].date()


class PeriodActivityRegistrationDeadlineValidator(RegistrationDeadlineValidator):
    @property
    def maxDate(self):
        return self.instance.deadline


class CompletedSlotsValidator(Validator):
    field = 'slots'
    code = 'slots'
    message = _('All time slots should have all required fields filled out.')

    def is_valid(self):
        return len([slot for slot in self.instance.slots.all() if not slot.is_complete]) == 0


class HasSlotValidator(Validator):
    field = 'slots'
    code = 'slots'
    message = _('Should have at least one time slot.')

    def is_valid(self):
        return self.instance.slots.count() > 0
