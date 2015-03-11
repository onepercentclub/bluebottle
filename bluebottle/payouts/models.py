from decimal import Decimal
from bluebottle.projects.models import PartnerOrganization
from bluebottle.sepa.sepa import SepaDocument, SepaAccount
from bluebottle.bb_payouts.models import BaseProjectPayout, BaseOrganizationPayout
from bluebottle.utils.utils import StatusDefinition
from djchoices.choices import DjangoChoices, ChoiceItem
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.conf import settings
from bluebottle.clients import properties


def get_fee_percentage(rule):
    return "{0}%".format(int(properties.PROJECT_PAYOUT_FEES[rule] * 100))


class ProjectPayout(BaseProjectPayout):

    class PayoutRules(DjangoChoices):
        """ Which rules to use to calculate fees. """
        beneath_threshold = ChoiceItem('beneath_threshold',
                                       label="{0} ({1})".format(_("Beneath minimal payout amount"),
                                                                get_fee_percentage('beneath_threshold')))
        fully_funded = ChoiceItem('fully_funded',
                                  label="{0} ({1})".format(_("Fully funded"),
                                                           get_fee_percentage('fully_funded')))
        not_fully_funded = ChoiceItem('not_fully_funded',
                                      label="{0} ({1})".format(_("Not fully funded"),
                                                               get_fee_percentage('not_fully_funded')))

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
        return self.amount_raised * Decimal(payable_rate)

    def calculate_amount_payable_rule_fully_funded(self, total):
        """
        Calculate the amount payable for fully_funded rule
        """
        payable_rate = 1 - properties.PROJECT_PAYOUT_FEES['fully_funded']
        return self.amount_raised * Decimal(payable_rate)

    def calculate_amount_payable_rule_not_fully_funded(self, total):
        """
        Calculate the amount payable for not_fully_funded rule
        """
        payable_rate = 1 - properties.PROJECT_PAYOUT_FEES['not_fully_funded']
        return self.amount_raised * Decimal(payable_rate)

    # Legacy payout rules

    def calculate_amount_payable_rule_old(self, total):
        """
        Calculate the amount payable for old rule
        """
        return self.amount_raised * Decimal(0.95)

    def calculate_amount_payable_rule_zero(self, total):
        """
        Calculate the amount payable for 0% rule
        """
        return self.amount_raised * Decimal(1)

    def calculate_amount_payable_rule_five(self, total):
        """
        Calculate the amount payable for 5% rule
        """
        return self.amount_raised * Decimal(0.95)

    def calculate_amount_payable_rule_seven(self, total):
        """
        Calculate the amount payable for 7% rule
        """
        return self.amount_raised * Decimal(0.93)

    def calculate_amount_payable_rule_twelve(self, total):
        """
        Calculate the amount payable for 5% rule
        """
        return self.amount_raised * Decimal(0.88)

    def calculate_amount_payable_rule_hundred(self, total):
        """
        Calculate the amount payable for 5% rule
        """
        return self.amount_raised * Decimal(0)

    def get_payout_rule(self):
        """
        Override this if you want different payout rules for different circumstances.
        e.g. project target reached, minimal amount reached.

        Default is just payout rule 5.
        """
        assert self.project

        # 1st of January 2014
        start_2014 = timezone.datetime(2014, 1, 1, tzinfo=timezone.utc)

        threshold = properties.MINIMAL_PAYOUT_AMOUNT

        if self.project.created >= start_2014:
            # New rules per 2014

            if self.project.amount_donated <= threshold:
                # Funding less then minimal payment amount.
                return self.PayoutRules.beneath_threshold
            elif self.project.amount_donated >= self.project.amount_asked:
                # Fully funded
                return self.PayoutRules.fully_funded
            else:
                # Not fully funded
                return self.PayoutRules.not_fully_funded

        # Campaign started before 2014
        # Always 5 percent
        return self.PayoutRules.five

    @classmethod
    def create_sepa_xml(cls, qs):
        """ Create a SEPA XML file for Payouts in QuerySet. """

        batch_id = timezone.datetime.strftime(timezone.now(), '%Y%m%d%H%I%S')

        sepa = SepaDocument(sepa_type='CT')

        sepa.set_initiating_party(
            name=settings.BANK_ACCOUNT_DONATIONS['name']
        )
        debtor = SepaAccount(
            name=settings.BANK_ACCOUNT_DONATIONS['name'],
            iban=settings.BANK_ACCOUNT_DONATIONS['iban'],
            bic=settings.BANK_ACCOUNT_DONATIONS['bic']
        )

        sepa.set_debtor(debtor)
        sepa.set_info(message_identification=batch_id, payment_info_id=batch_id)
        sepa.set_initiating_party(name=settings.BANK_ACCOUNT_DONATIONS['name'])

        now = timezone.now()

        for payout in qs.all():
            payout.status = StatusDefinition.IN_PROGRESS
            payout.submitted = now
            payout.save()
            creditor = SepaAccount(
                name=payout.receiver_account_name,
                iban=payout.receiver_account_iban,
                bic=payout.receiver_account_bic
            )

            sepa.add_credit_transfer(
                creditor=creditor,
                amount=payout.amount_payable,
                creditor_payment_id=payout.invoice_reference
            )

        return sepa.as_xml()


class OrganizationPayout(BaseOrganizationPayout):

    @classmethod
    def create_sepa_xml(cls, qs):
        """ Create a SEPA XML file for OrganizationPayouts in QuerySet. """

        batch_id = timezone.datetime.strftime(timezone.now(), '%Y%m%d%H%I%S')

        sepa = SepaDocument(sepa_type='CT')

        sepa.set_initiating_party(
            name=settings.BANK_ACCOUNT_DONATIONS['name']
        )
        debtor = SepaAccount(
            name=settings.BANK_ACCOUNT_DONATIONS['name'],
            iban=settings.BANK_ACCOUNT_DONATIONS['iban'],
            bic=settings.BANK_ACCOUNT_DONATIONS['bic']
        )

        sepa.set_debtor(debtor)
        sepa.set_info(
            message_identification=batch_id, payment_info_id=batch_id)
        sepa.set_initiating_party(name=settings.BANK_ACCOUNT_DONATIONS['name'])

        now = timezone.now()

        for payout in qs.all():
            payout.status = StatusDefinition.IN_PROGRESS
            payout.submitted = now
            payout.save()
            creditor = SepaAccount(
                name=settings.BANK_ACCOUNT_ORGANISATION['name'],
                iban=settings.BANK_ACCOUNT_ORGANISATION['iban'],
                bic=settings.BANK_ACCOUNT_ORGANISATION['bic']
            )

            sepa.add_credit_transfer(
                creditor=creditor,
                amount=payout.payable_amount_incl,
                creditor_payment_id=payout.invoice_reference
            )

        return sepa.as_xml()
