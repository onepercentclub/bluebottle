from django.utils.translation import ugettext_lazy as _

from bluebottle.utils.models import Validator


class UniqueTitleValidator(Validator):
    field = 'title'
    code = 'required'
    message = _('The title must be unique')

    def is_valid(self):
        return not self.instance.__class__.objects.exclude(
            pk=self.instance.pk
        ).filter(
            status='approved',
            title=self.instance.title
        ).count()

