from decimal import Decimal
from moneyed import Money

from django.db import models
from django.db.models.aggregates import Sum
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.translation import ugettext as _
from django_extensions.db.fields import CreationDateTimeField

from bluebottle.utils.fields import MoneyField


class BaseJournal(models.Model):
    """
    Journal can not be changed, date is the creation date and is fixed.

    Amount can be positive or negative.

    Description can hold any remarks that someone wants to add when manually making a journal

    Each subclass from this BaseJournal should have these properties:
    - related_model_field_name, for example 'donation'
      which is used to determine the related model self.donation
    - related_model_amount_field_name, for example 'amount', which is used
      to determine the total amount in the related model, that should equal with
      the total amount of all Journals that are related to that model.

    get_user_reference() should be overridden whenever an user_reference
    should be saved on each Journal. This could be: self.donation.user_id
    """
    amount = MoneyField(_("amount"))
    user_reference = models.CharField('user reference', max_length=100,  blank=True)
    description = models.CharField(max_length=400, blank=True)

    date = CreationDateTimeField(_("Created"))

    class Meta:
        abstract = True

    related_model_field_name = None
    related_model_amount_field_name = None

    @property
    def related_model(self):
        return getattr(self, self.related_model_field_name)

    def get_related_model_amount(self):
        related_model = self.related_model
        return getattr(related_model, self.related_model_amount_field_name)

    def get_user_reference(self):
        return ''

    def get_journal_total(self):
        """
        Return the total amount for all Journals
        belonging to the current Donation, ProjectPayout or OrganizationPayout,
        """
        related_model_name = self.related_model_field_name  # 'donation'
        filter_ = {related_model_name: self.related_model}  # {'donation': self.donation}

        return self.related_model.journal_set.all().filter(**filter_).aggregate(
            Sum('amount'))['amount__sum'] or 0

    def save(self, *args, **kwargs):
        # could be prefilled via the admin by the (staff) user that does a change
        if not self.user_reference:
            self.user_reference = self.get_user_reference()

        super(BaseJournal, self).save(*args, **kwargs)


class DonationJournal(BaseJournal):
    donation = models.ForeignKey('donations.Donation',
                                 related_name='journal_set',)

    related_model_field_name = 'donation'
    related_model_amount_field_name = 'amount'

    def get_user_reference(self):
        try:
            return self.donation.user.email  # user is property on Donation
        except AttributeError:
            return ''


class OrganizationPayoutJournal(BaseJournal):
    payout = models.ForeignKey('payouts.OrganizationPayout',
                               related_name='journal_set',)

    related_model_field_name = 'payout'
    related_model_amount_field_name = 'payable_amount_incl'


class ProjectPayoutJournal(BaseJournal):
    payout = models.ForeignKey('payouts.ProjectPayout',
                               related_name='journal_set',)

    related_model_field_name = 'payout'
    related_model_amount_field_name = 'amount_payable'  # or amount raised


class OrderPaymentJournal(models.Model):

    """
    Journal that's used only to report something odd.

    Do not inherit from BaseJournal, because we don't want the signal behaviour.
    """
    amount = MoneyField(_("amount"))
    user_reference = models.CharField('user reference', max_length=100,  blank=True, editable=False)
    description = models.CharField(max_length=400, blank=True)
    order_payment = models.ForeignKey('payments.OrderPayment', related_name='journals')

    date = CreationDateTimeField(_("Created"))


@receiver(post_save, sender=DonationJournal)
@receiver(post_save, sender=OrganizationPayoutJournal)
@receiver(post_save, sender=ProjectPayoutJournal)
def update_related_model_when_journal_is_saved(sender, instance, created, **kwargs):
    """
    After a journal is saved, the related model (a Donation or Payout)
    might need to be updated with the correction that is added via this new
    Journal.

    the value of 'related_model_amount_field_name' on the related model should
    be the same as the total of all Journals that belong to that model.
    """
    journal_total = instance.get_journal_total()
    related_model_total = instance.get_related_model_amount()

    if journal_total != related_model_total:
        related_model = instance.related_model
        amount_key = instance.related_model_amount_field_name

        setattr(related_model, amount_key, journal_total)  # journal total is leading
        related_model.save()


def create_journal_for_sender(sender, instance, created, data_migration=None):
    """
    data_migration contains a dictionary when this function is called from
    a data migration, because there is no way to get the related names as
    properties form the Django model.

    in all other cases it should stay None
    """
    if data_migration:
        journal_class = data_migration.get('journal_class')
        related_model_name = data_migration.get('related_model_name')
        related_model_amount_field_name = data_migration.get('related_model_amount_field_name')
    else:
        from bluebottle.donations.models import Donation
        from bluebottle.payouts.models import ProjectPayout, OrganizationPayout

        MAPPING = {
            Donation: DonationJournal,
            ProjectPayout: ProjectPayoutJournal,
            OrganizationPayout: OrganizationPayoutJournal,
        }
        journal_class = MAPPING.get(sender)
        related_model_name = journal_class.related_model_field_name
        related_model_amount_field_name = journal_class.related_model_amount_field_name

    amount_instance = getattr(instance, related_model_amount_field_name)
    journals = instance.journal_set.all()

    if (not created) and journals.exists():
        if data_migration:
            # never add journals from datamigration when there already exists one
            return

        # instance is created already, and there is at least one journal already
        # so it is a modified Payout or Donation, check if the amount was changed,
        # and add the correction when needed
        journal = journals.first()  # even when there are more, the get_journal_total will return the correct value
        journal_amount = journal.get_journal_total()

        if hasattr(amount_instance, 'amount'):
            amount_instance = amount_instance.amount
        diff = amount_instance - journal_amount
        if diff == Decimal():
            return  # dont save, or should a new journal be made when amount is not changed?Hry
        journal_date = instance.updated
        journal_amount = Money(diff, journal.amount.currency)
    else:
        journal_date = instance.created
        journal_amount = amount_instance

    kwargs = {
        related_model_name: instance,
        'amount': journal_amount,
        'date': journal_date
    }
    journal_class.objects.create(**kwargs)
