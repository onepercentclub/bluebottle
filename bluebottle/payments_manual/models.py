from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _

from bluebottle.utils.fields import MoneyField
from bluebottle.utils.utils import StatusDefinition

from bluebottle.payments.models import Payment

# For the purpose of this module, see the docstring in __init__.py


class ManualPayment(Payment):
    amount = MoneyField(_("amount"), editable=False)
    bank_transaction = models.ForeignKey('accounting.BankTransaction', editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False)  # track user who entered this record

    class Meta:
        verbose_name = _('manual payment')
        verbose_name_plural = _('manual payments')

    def __init__(self, *args, **kwargs):
        self.status = StatusDefinition.SETTLED  # this is only created after the money has been received
        super(ManualPayment, self).__init__(*args, **kwargs)

    def get_fee(self):
        return 0
