from datetime import timedelta

from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from bluebottle.utils.models import Validator


class KYCReadyValidator(Validator):
    """
    Is the connected bank account verified by the external KYC check (e.g. Stripe)?
    For other PSPs we just assume all is ok for submitting, but required after
    """

    code = 'kyc'
    message = _('Make sure your payout account is verified')
    field = 'kyc'

    def is_valid(self):
        return self.instance.bank_account and self.instance.bank_account.status == 'verified'


class DeadlineValidator(Validator):
    code = 'deadline'
    message = _('Make sure the deadline is in the future.')
    field = 'deadline'

    def is_valid(self):
        return (
            self.instance.status in ('submitted', 'needs_work', 'draft') or
            self.instance.duration or
            (
                self.instance.deadline and
                now() < self.instance.deadline
            )
        )


class DeadlineMaxValidator(Validator):
    code = 'deadline'
    message = _('The deadline should not be more then 60 days in the future')
    field = 'deadline'

    def is_valid(self):
        return (
            self.instance.status in ('submitted', 'needs_work', 'draft') or
            self.instance.duration or
            (
                self.instance.deadline and
                self.instance.deadline <= now() + timedelta(days=60)
            )
        )


class BudgetLineValidator(Validator):
    code = 'budgetlines'
    message = _('Please specify a budget')
    field = 'budgetlines'

    def is_valid(self):
        return len(self.instance.budget_lines.all()) > 0


class TargetValidator(Validator):
    code = 'target'
    message = _('Please specify a target')
    field = 'target'

    def is_valid(self):
        if self.instance.target is None:
            return False
        if self.instance.target.amount <= 0:
            return False
        return True
