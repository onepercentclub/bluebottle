from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext_lazy as _

from djchoices.choices import DjangoChoices, ChoiceItem
from polymorphic.models import PolymorphicModel

from bluebottle.bb_payouts.models import (BaseProjectPayout,
                                          BaseOrganizationPayout)
from bluebottle.clients import properties
from bluebottle.utils.models import BasePlatformSettings


class PayoutAccount(PolymorphicModel):

    type = 'base'
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)
    user = models.ForeignKey('members.Member')


class PayoutMethod(models.Model):
    TYPES = [
        ('plain-payout', 'Plain'),
        ('stripe-base', 'Stripe')
    ]
    payout_settings = models.ForeignKey('payouts.PayoutPlatformSettings')
    method = models.CharField(max_length=100, choices=TYPES)
    countries = models.ManyToManyField('geo.Country', null=True, blank=True)


class PayoutPlatformSettings(BasePlatformSettings):
    pass


# Legacy Payouts models

class ProjectPayout(BaseProjectPayout):
    class PayoutRules(DjangoChoices):
        """ Which rules to use to calculate fees. """
        beneath_threshold = ChoiceItem('beneath_threshold',
                                       label=_("Beneath minimal payout amount"))
        fully_funded = ChoiceItem('fully_funded', label=_("Fully funded"))
        not_fully_funded = ChoiceItem('not_fully_funded',
                                      label=_("Not fully funded"))

        # Legacy payout rules
        old = ChoiceItem('old', label=_("Legacy: Old 1%/5%"))
        zero = ChoiceItem('zero', label=_("Legacy: 0%"))
        five = ChoiceItem('five', label=_("Legacy: 5%"))
        seven = ChoiceItem('seven', label=_("Legacy: 7%"))
        twelve = ChoiceItem('twelve', label=_("Legacy: 12%"))
        hundred = ChoiceItem('hundred', label=_("Legacy: 100%"))
        unknown = ChoiceItem('unknown', label=_("Legacy: Unknown"))
        other = ChoiceItem('other', label=_("Legacy: Other"))

    # Payout rules

    def calculate_amount_payable_rule_beneath_threshold(self, total):
        """
        Calculate the amount payable for beneath_threshold rule
        """
        payable_rate = 1 - properties.PROJECT_PAYOUT_FEES['beneath_threshold']
        return total * Decimal(payable_rate)

    def calculate_amount_payable_rule_fully_funded(self, total):
        """
        Calculate the amount payable for fully_funded rule
        """
        payable_rate = 1 - properties.PROJECT_PAYOUT_FEES['fully_funded']
        return total * Decimal(payable_rate)

    def calculate_amount_payable_rule_not_fully_funded(self, total):
        """
        Calculate the amount payable for not_fully_funded rule
        """
        payable_rate = 1 - properties.PROJECT_PAYOUT_FEES['not_fully_funded']
        return total * Decimal(payable_rate)

    # Legacy payout rules

    def calculate_amount_payable_rule_old(self, total):
        """
        Calculate the amount payable for old rule
        """
        return total * Decimal(0.95)

    def calculate_amount_payable_rule_zero(self, total):
        """
        Calculate the amount payable for 0% rule
        """
        return total * Decimal(1)

    def calculate_amount_payable_rule_five(self, total):
        """
        Calculate the amount payable for 5% rule
        """
        return total * Decimal(0.95)

    def calculate_amount_payable_rule_seven(self, total):
        """
        Calculate the amount payable for 7% rule
        """
        return total * Decimal(0.93)

    def calculate_amount_payable_rule_twelve(self, total):
        """
        Calculate the amount payable for 5% rule
        """
        return total * Decimal(0.88)

    def calculate_amount_payable_rule_hundred(self, total):
        """
        Calculate the amount payable for 5% rule
        """
        return total * Decimal(0)

    def get_payout_rule(self):
        """
        Override this if you want different payout rules for different circumstances.
        e.g. project target reached, minimal amount reached.
        """
        assert self.project

        threshold = properties.MINIMAL_PAYOUT_AMOUNT

        if self.project.amount_donated.amount <= threshold:
            # Funding less then minimal payment amount.
            return self.PayoutRules.beneath_threshold
        elif self.project.amount_donated >= self.project.amount_asked:
            # Fully funded
            return self.PayoutRules.fully_funded
        else:
            # Not fully funded
            return self.PayoutRules.not_fully_funded


class OrganizationPayout(BaseOrganizationPayout):
    def _get_organization_fee(self):
        """
        Calculate and return the organization fee for Payouts within this
        OrganizationPayout's period, including VAT.

        Note: this should *only* be called internally.
        """
        # Get Payouts
        payouts = ProjectPayout.objects.filter(
            completed__gte=self.start_date,
            completed__lte=self.end_date
        )

        # Aggregate value
        aggregate = payouts.aggregate(models.Sum('organization_fee'))

        # Return aggregated value or 0.00
        fee = aggregate.get(
            'organization_fee__sum', Decimal('0.00')
        ) or Decimal('0.00')

        return fee
