import csv
import decimal

import datetime
from decimal import Decimal
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone
from django.utils.translation import ugettext as _
from django_extensions.db.fields import (ModificationDateTimeField,
                                         CreationDateTimeField)
from bluebottle.bb_payouts.exceptions import PayoutException
from bluebottle.bb_payouts.utils import money_from_cents
from bluebottle.bb_projects.fields import MoneyField
from bluebottle.payments.models import OrderPayment
from bluebottle.utils.utils import StatusDefinition


from djchoices.choices import DjangoChoices, ChoiceItem

from .utils import calculate_vat, calculate_vat_exclusive, date_timezone_aware
from bluebottle.utils.model_dispatcher import get_project_model, get_donation_model, get_project_payout_model

PROJECT_MODEL = get_project_model()
DONATION_MODEL = get_donation_model()

class InvoiceReferenceMixin(models.Model):
    """
    Mixin for generating an invoice reference.
    """

    invoice_reference = models.CharField(max_length=100)

    class Meta:
        abstract = True

    def generate_invoice_reference(self):
        """ Generate invoice reference. """

        assert self.id, 'Object should be saved first.'

        return unicode(self.id)

    def update_invoice_reference(self, auto_save=False, save=True):
        """
        Generate and save (when save=True) invoice reference.
        Automatically saves to generate an id when auto_save is set.
        """

        if auto_save and not self.id:
            # Save to generate self.id
            super(InvoiceReferenceMixin, self).save()

        assert not self.invoice_reference, 'Invoice reference already set!'

        self.invoice_reference = self.generate_invoice_reference()

        if save:
            super(InvoiceReferenceMixin, self).save()


class CompletedDateTimeMixin(models.Model):
    """
    Mixin for Payout objects logging when the status is changed
    from progress to completed in a 'completed' field.
    """

    # The timestamp the order changed to completed. This is auto-set in the save() method.
    completed = models.DateField(
        _("Closed"), blank=True, null=True, help_text=_(
            'Book date when the bank transaction was confirmed and '
            'the payout has been set to completed.'
        )
    )

    class Meta:
        abstract = True

    def clean(self):
        """ Validate completed/completed date consistency. """

        if self.completed and self.status != StatusDefinition.SETTLED:
            raise ValidationError(
                _('Closed date is set but status is not completed.')
            )

    def save(self, *args, **kwargs):
        if self.status == StatusDefinition.SETTLED and not self.completed:
            # No completed date was set and our current status is completed
            self.completed = timezone.now()

        super(CompletedDateTimeMixin, self).save(*args, **kwargs)


class PayoutBase(InvoiceReferenceMixin, CompletedDateTimeMixin, models.Model):
    """
    Common abstract base class for ProjectPayout and OrganizationPayout.
    """
    STATUS_CHOICES = (
        (StatusDefinition.NEW, _('New')),
        (StatusDefinition.IN_PROGRESS, _('In progress')),
        (StatusDefinition.SETTLED, _('Settled')),
    )

    planned = models.DateField(_("Planned"), help_text=_("Date on which this batch should be processed."))

    status = models.CharField(_("status"), max_length=20, choices=STATUS_CHOICES, default=StatusDefinition.NEW)

    created = CreationDateTimeField(_("created"))
    updated = ModificationDateTimeField(_("updated"))

    submitted = models.DateTimeField(_("submitted"), blank=True, null=True)

    class Meta:
        abstract = True

    def _get_old_status(self):
        """
        Get previous status based on state change logs.
        """

        assert self.pk

        try:
            latest_state_change = self.payout_logs.latest()
            return latest_state_change.new_status

        except ObjectDoesNotExist:
            # First state change, no previous state
            return None

    def _log_status_change(self):
        """
        Log the change from one status to another.
        """

        old_status = self._get_old_status()

        if old_status != self.status:
            # Create log entry
            log_entry = self.payout_logs.model(
                payout=self,
                old_status=old_status, new_status=self.status
            )
            log_entry.save()

            return log_entry

    def save(self, *args, **kwargs):
        """
        Make sure we log a state change after saving.
        """

        result = super(PayoutBase, self).save(*args, **kwargs)

        self._log_status_change()

        return result


class PayoutLogBase(models.Model):
    """
    Abstract base class for logging state changes.
    Requires a 'payout' ForeignKey with related_name='log_set' to be defined.
    """

    class Meta:
        verbose_name = _('state change')
        verbose_name_plural = _('state changes')
        abstract = True

        ordering = ['-created']
        get_latest_by = 'created'

    STATUS_CHOICES = (
        (StatusDefinition.NEW, _("New")),
        (StatusDefinition.IN_PROGRESS, _("In progress")),
        (StatusDefinition.SETTLED, _("Settled"))
    )

    created = CreationDateTimeField(_("date"))

    old_status = models.CharField(
        _("old status"), max_length=20, choices=STATUS_CHOICES,
        blank=True, null=True
    )

    new_status = models.CharField(
        _("new status"), max_length=20, choices=STATUS_CHOICES,
    )

    def __unicode__(self):
        return _(
            u'Status change of \'%(payout)s\' on %(created)s from %(old_status)s to %(new_status)s' % {
                'payout': unicode(self.payout),
                'created': self.created.strftime('%d-%m-%Y'),
                'old_status': self.old_status,
                'new_status': self.new_status,
            }
        )


class BaseProjectPayout(PayoutBase):
    """
    A projects is payed after the campaign deadline is hit..
    Project payouts are checked manually.
    """

    class PayoutRules(DjangoChoices):
        """ Which rules to use to calculate fees. """
        beneath_threshold = ChoiceItem('beneath_threshold', label=_("Beneath minimal payout amount"))
        fully_funded = ChoiceItem('fully_funded', label=_("Fully funded"))
        not_fully_funded = ChoiceItem('not_fully_funded', label=_("Not fully funded"))

    project = models.ForeignKey(settings.PROJECTS_PROJECT_MODEL)

    payout_rule = models.CharField(_("Payout rule"), max_length=20,  help_text=_("The payout rule for this project."))

    amount_raised = MoneyField(_("amount raised"),
                               help_text=_('Amount raised when Payout was created or last recalculated.'))

    organization_fee = MoneyField(_("organization fee"),
                                  help_text=_('Fee subtracted from amount raised for the organization.'))

    amount_payable = MoneyField(_("amount payable"),
                                help_text=_('Payable amount; raised amount minus organization fee.'))

    sender_account_number = models.CharField(max_length=100)
    receiver_account_number = models.CharField(max_length=100, blank=True)
    receiver_account_iban = models.CharField(max_length=100, blank=True)
    receiver_account_bic = models.CharField(max_length=100, blank=True)
    receiver_account_name = models.CharField(max_length=100)
    receiver_account_city = models.CharField(max_length=100)
    receiver_account_country = models.CharField(max_length=100, null=True)

    description_line1 = models.CharField(max_length=100, blank=True, default="")
    description_line2 = models.CharField(max_length=100, blank=True, default="")
    description_line3 = models.CharField(max_length=100, blank=True, default="")
    description_line4 = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        get_latest_by = 'created'
        ordering = ['-created']
        abstract = True

    @property
    def amount_pending(self):
        return self.get_amount_pending()

    @property
    def amount_safe(self):
        return self.get_amount_safe()

    @property
    def amount_failed(self):
        return self.get_amount_failed()

    @property
    def percent(self):
        if not self.amount_payable: return "-"
        
        return "{}%".format(round(((self.amount_raised - self.amount_payable) / self.amount_raised)*100, 1))
    
    def get_payout_rule(self):
        """
        Override this if you want different payout rules for different circumstances.
        e.g. project target reached, minimal amount reached.

        Default is just payout rule 5.
        """
        return self.PayoutRules.five

    def calculate_amount_payable_rule_five(self, total):
        """
        Calculate the amount payable for 5% rule
        """
        return self.amount_raised * Decimal(0.95)

    def calculate_amounts(self, save=True):
        """
        Calculate amounts according to payment_rule.

        Updates:
          - payout_rule
          - amount_raised
          - organization_fee
          - amount_payable

        Should only be called for Payouts with status 'new'.
        """
        assert self.status == StatusDefinition.NEW, 'Can only recalculate for new Payout.'

        # Set payout rule if none set.
        if not self.payout_rule:
            self.payout_rule = self.get_payout_rule()

        self.amount_raised = self.get_amount_raised()

        calculator_name = "calculate_amount_payable_rule_{0}".format(self.payout_rule)
        try:
            calculator = getattr(self, "calculate_amount_payable_rule_{0}".format(self.payout_rule))
        except AttributeError:
            message = "Missing calculator for payout rule '{0}': '{1}'".format(self.payout_rule, calculator_name)
            raise PayoutException(message)

        self.amount_payable = Decimal(round(calculator(self.get_amount_raised()), 2))

        if self.payout_rule is 'beneath_threshold' and not self.amount_pending:
            self.status = StatusDefinition.SETTLED

        self.organization_fee = self.amount_raised - self.amount_payable

        if save:
            self.save()

    def generate_invoice_reference(self):
        """
        Generate invoice reference from project and payout id's.
        """
        assert self.id
        assert self.project
        assert self.project.id

        return u'%d-%d' % (self.project.id, self.id)

    def get_amount_raised(self):
        """
        Real time amount of raised ('paid', 'pending') donations.
        """
        return self.project.amount_donated

    def get_amount_safe(self):
        """
        Real time amount of safe ('paid') donations.
        """
        return self.project.amount_safe

    def get_amount_pending(self):
        """
        Real time amount of pending donations.
        """
        return self.project.amount_pending

    def get_amount_failed(self):
        """
        Real time difference between saved amount_raised, safe and pending.

        Note: amount_raised is the saved property, other values are real time.
        """

        amount_safe = self.get_amount_safe()
        amount_pending = self.get_amount_pending()

        amount_failed = self.amount_raised - amount_safe - amount_pending

        if amount_failed <= decimal.Decimal('0.00'):
            # Should never be less than 0
            return decimal.Decimal('0.00')

        return amount_failed

    def __unicode__(self):
        date = self.created.strftime('%d-%m-%Y')
        return  self.invoice_reference + " : " + date + " : " + self.receiver_account_number + " : EUR " + str(self.amount_payable)


class ProjectPayoutLog(PayoutLogBase):
    payout = models.ForeignKey(settings.PAYOUTS_PROJECTPAYOUT_MODEL, related_name='payout_logs')


class BaseOrganizationPayout(PayoutBase):
    """
    Payouts for organization fees minus costs to the organization spanning
    a particular span of time.

    Organization fees are calculated from completed Payouts to projects and
    are originally including VAT.

    PSP costs are calculated from orders and are originally excluding VAT.

    Other costs (i.e. international banking fees) can be manually specified
    either excluding or including VAT.

    Note: Start and end dates are inclusive.
    """
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'))

    organization_fee_excl = MoneyField(_('organization fee excluding VAT'))
    organization_fee_vat = MoneyField(_('organization fee VAT'))
    organization_fee_incl = MoneyField(_('organization fee including VAT'))

    psp_fee_excl = MoneyField(_('PSP fee excluding VAT'))
    psp_fee_vat = MoneyField(_('PSP fee VAT'))
    psp_fee_incl = MoneyField(_('PSP fee including VAT'))

    other_costs_excl = MoneyField(
        _('other costs excluding VAT'), default=decimal.Decimal('0.00'),
        help_text=_(
            'Set either this value or inclusive VAT, make sure recalculate afterwards.'
        )
    )
    other_costs_vat = MoneyField(
        _('other costs VAT'), default=decimal.Decimal('0.00'))
    other_costs_incl = MoneyField(
        _('other costs including VAT'), default=decimal.Decimal('0.00'),
        help_text=_(
            'Set either this value or exclusive VAT, make sure recalculate afterwards.'
        )
    )

    payable_amount_excl = MoneyField(_('payable amount excluding VAT'))
    payable_amount_vat = MoneyField(_('payable amount VAT'))
    payable_amount_incl = MoneyField(_('payable amount including VAT'))

    class Meta:
        unique_together = ('start_date', 'end_date')
        get_latest_by = 'end_date'
        ordering = ['start_date']
        abstract = True

    def _get_organization_fee(self):
        """
        Calculate and return the organization fee for Payouts within this
        OrganizationPayout's period, including VAT.

        Note: this should *only* be called internally.
        """
        PROJECT_PAYOUT_MODEL = get_project_payout_model()
        # Get Payouts
        payouts = PROJECT_PAYOUT_MODEL.objects.filter(
            completed__gte=self.start_date,
            completed__lte=self.end_date
        )

        # Aggregate value
        aggregate = payouts.aggregate(models.Sum('organization_fee'))

        # Return aggregated value or 0.00
        fee = aggregate.get(
            'organization_fee__sum', decimal.Decimal('0.00')
        ) or decimal.Decimal('0.00')

        return fee

    def _get_psp_fee(self):
        """
        Calculate and return Payment Service Provider fee from
        payments relating through orders to donations which became irrevocably
        paid during the OrganizationPayout period, excluding VAT.

        Note: this should *only* be called internally.
        """
        # Allowed payment statuses (statusus generating fees)
        # In apps.cowry_docdata.adapters it appears that fees are only
        # calculated for the paid status, with implementation for chargedback
        # coming. There are probably other fees
        allowed_statuses = (
            StatusDefinition.SETTLED,
            StatusDefinition.CHARGED_BACK,
            StatusDefinition.REFUNDED,
        )

        payments = OrderPayment.objects.filter(
            status__in=allowed_statuses
        )

        # Do a silly trick by filtering the date the donation became paid
        # (the only place where the Docdata closed/paid status is matched).
        # payments = payments.order_by('order__closed')
        payments = payments.filter(
            closed__gte=date_timezone_aware(self.start_date),
            closed__lte=date_timezone_aware(self.end_date)
        )

        # Make sure this does not create additional objects
        payments = payments.distinct()

        # Aggregate the variable fees and count the amount of payments
        aggregate = payments.aggregate(models.Sum('transaction_fee'))

        # Aggregated value (in cents) or 0
        fee = aggregate.get('transaction_fee__sum', 0) or 0

        return Decimal(fee)

    def calculate_amounts(self, save=True):
        """
        Calculate amounts. If save=True, saves the result.

        Should only be called for Payouts with status 'new'.
        """
        assert self.status == StatusDefinition.NEW, 'Can only recalculate for new Payout.'

        # Calculate original values
        self.organization_fee_incl = self._get_organization_fee()
        self.psp_fee_excl = self._get_psp_fee()

        assert isinstance(self.organization_fee_incl, decimal.Decimal)
        assert isinstance(self.psp_fee_excl, decimal.Decimal)

        # VAT calculations
        self.organization_fee_excl = calculate_vat_exclusive(self.organization_fee_incl)
        self.organization_fee_vat = self.organization_fee_incl - self.organization_fee_excl

        self.psp_fee_vat = calculate_vat(self.psp_fee_excl)
        self.psp_fee_incl = self.psp_fee_excl + self.psp_fee_vat

        # Conditionally calculate VAT for other_costs
        if self.other_costs_incl and not self.other_costs_excl:
            # Inclusive VAT set, calculate exclusive
            self.other_costs_excl = calculate_vat_exclusive(self.other_costs_incl)
            self.other_costs_vat = self.other_costs_incl - self.other_costs_excl

        elif self.other_costs_excl and not self.other_costs_incl:
            # Exclusive VAT set, calculate inclusive
            self.other_costs_vat = calculate_vat(self.other_costs_excl)
            self.other_costs_incl = self.other_costs_excl + self.other_costs_vat

        # Calculate payable amount
        self.payable_amount_excl =  (
            self.organization_fee_excl - self.psp_fee_excl - self.other_costs_excl
        )
        self.payable_amount_vat =  (
            self.organization_fee_vat - self.psp_fee_vat - self.other_costs_vat
        )
        self.payable_amount_incl = (
            self.organization_fee_incl - self.psp_fee_incl - self.other_costs_incl
        )

        if save:
            self.save()

    def clean(self):
        """ Validate date span consistency. """

        # End date should lie after start_date
        if self.start_date >= self.end_date:
            raise ValidationError(_('Start date should be earlier than date.'))

        if not self.id:
            # Validation for new objects

            # There should be no holes in periods between payouts
            try:
                latest = self.__class__.objects.latest()
                next_date = latest.end_date + datetime.timedelta(days=1)

                if next_date != self.start_date:
                    raise ValidationError(_('The next payout period should start the day after the end of the previous period.'))

            except self.__class__.DoesNotExist:
                # No earlier payouts exist
                pass

        else:
            # Validation for existing objects

            # Check for consistency before changing into 'progress'.
            old_status = self.__class__.objects.get(id=self.id).status

            if (
                old_status == StatusDefinition.NEW and
                self.status == StatusDefinition.IN_PROGRESS
            ):
                # Old status: new
                # New status: progress

                # Check consistency of other costs
                if (
                    self.other_costs_incl - self.other_costs_excl != self.other_costs_vat
                ):
                    raise ValidationError(_('Other costs have changed, please recalculate before progessing.'))

        # TODO: Prevent overlaps

        super(BaseOrganizationPayout, self).clean()

    def save(self, *args, **kwargs):
        """
        Calculate values on first creation and generate invoice reference.
        """

        if not self.id:
            # No id? Not previously saved

            if self.status == StatusDefinition.NEW:
                # This exists mainly for testing reasons, payouts should
                # always be created new
                self.calculate_amounts(save=False)

            if not self.invoice_reference:
                # Conditionally creat invoice reference
                self.update_invoice_reference(auto_save=True, save=False)

        super(BaseOrganizationPayout, self).save(*args, **kwargs)

    def generate_invoice_reference(self):
        """ Generate invoice reference from project and payout id's. """
        assert self.id

        return u'%(year)d-OP%(payout_id)04d' % {
            'year': self.created.year,
            'payout_id': self.id
        }

    def __unicode__(self):
        return u'%(invoice_reference)s from %(start_date)s to %(end_date)s' % {
            'invoice_reference': self.invoice_reference,
            'start_date': self.start_date,
            'end_date': self.end_date
        }


class OrganizationPayoutLog(PayoutLogBase):
    payout = models.ForeignKey(settings.PAYOUTS_ORGANIZATIONPAYOUT_MODEL, related_name='payout_logs')


# Connect signals after defining models
# Ref:  http://stackoverflow.com/a/9851875
# Note: for newer Django, put this in module initialization code
# https://docs.djangoproject.com/en/dev/topics/signals/#django.dispatch.receiver
from .signals import create_payout_finished_project

post_save.connect(create_payout_finished_project, weak=False, sender=PROJECT_MODEL)

