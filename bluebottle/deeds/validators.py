from django.utils.translation import ugettext_lazy as _

from bluebottle.utils.models import Validator


class EndDateValidator(Validator):
    field = 'end'
    code = 'end-date'
    message = _('The end date should be after the start date')

    def is_valid(self):
        return (
            not self.instance.start or
            not self.instance.end or
            self.instance.start < self.instance.end
        )
