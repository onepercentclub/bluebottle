from moneyed.classes import Money

from bluebottle.members.models import Member
from bluebottle.payouts.models import ProjectPayout
from bluebottle.donations.models import Donation # can not be imported befor ProjectPayout
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.payouts import ProjectPayoutFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase

from ..models import DonationJournal, ProjectPayoutJournal

from datetime import date
from django.utils import timezone
from decimal import Decimal


class JournalModelTests(BluebottleTestCase):
    """

    note: Donation and payout updates when a journal is made via the admin
    will be tested in journal/tests/test_admin
    """

    def setUp(self):
        super(JournalModelTests, self).setUp()
        self.init_projects() # loads fixture for project phases

        self.assertEqual(Member.objects.count(), 0)

        self.project_owner = BlueBottleUserFactory.create(email='projectowner@example.com', primary_language='en')
        self.assertEqual(Member.objects.count(), 1)

        self.project = ProjectFactory.create(amount_asked=500, owner=self.project_owner)
        self.user = BlueBottleUserFactory.create(first_name='Jane', email='te@st.nl')

        journals = DonationJournal.objects.all()
        self.assertEqual(journals.count(), 0)

    def _get_only_one_from_db(self, model_name):
        objects = model_name.objects.all()
        self.assertEqual(objects.count(), 1)
        return objects.first()

    def _check_if_journal_total_equals_value(self, journal, value=None):
        """
        Final check to see if the journal total is the same as the
        amount on the related model.
        When 'value' is specified, check if it is the same as the other amounts
        """
        journal_amount = journal.get_journal_total()
        related_model_value = journal.get_related_model_amount()
        self.assertEqual(related_model_value, journal_amount)

        if value:
            self.assertEqual(journal_amount, value)

    def test_journal_created_when_donation_is_made(self):
        """
        Create a Donation, and check if it results in a Journal.

        Then create a Journal, and check if the Donation is updated.
        Do this also for a negative value
        """
        self.assertEqual(DonationJournal.objects.all().count(), 0)

        self.assertEqual(Member.objects.count(), 2)  # self.user and self.project_owner
        # creates another user for fundraiser
        self.donation = DonationFactory.create(user=self.user,
                                               amount=Money(100, 'EUR'),
                                               project=self.project,
                                               order__user=self.user)
        self.assertEqual(Member.objects.count(), 4)

        # creation of a donation should always result in the creation of a journal
        donation_from_db = self._get_only_one_from_db(Donation)
        journal_from_db = self._get_only_one_from_db(DonationJournal)

        self.assertEqual(journal_from_db.donation, donation_from_db)
        self.assertEqual(donation_from_db.amount.amount, Decimal('100'))
        self.assertEqual(journal_from_db.amount.amount, Decimal('100'))

        # #### Create a Journal, check if it results in an updated Donation ##### #
        journal = DonationJournal.objects.create(donation = self.donation,
                                                 amount = Money(50, 'EUR'))
        new_journal_pk = journal.pk
        self.assertEqual(DonationJournal.objects.all().count(), 2)
        new_journal_from_db = DonationJournal.objects.get(pk=new_journal_pk)

        self.assertEqual(new_journal_from_db.user_reference, 'te@st.nl')  # should be auto filled with donation user
        self.assertEqual(new_journal_from_db.description, '')  # should be blank

        self.assertEqual(new_journal_from_db.date.date(), date.today())  # date today
        self.assertEqual(new_journal_from_db.amount.amount, Decimal('50'))

        # the donation should be updated with the amount added via the journal
        donation_from_db = self._get_only_one_from_db(Donation)
        self.assertEqual(donation_from_db.amount.amount, Decimal('150'))  # change to new amount

        self._check_if_journal_total_equals_value(new_journal_from_db, donation_from_db.amount.amount)

        # Change the Donation, and check if a new Journal is created
        donation_from_db.amount.amount = Decimal('145')
        donation_from_db.save()
        self.assertEqual(DonationJournal.objects.all().count(), 3)
        new_journal = DonationJournal.objects.all().last()  # the latest is the newest
        self.assertEqual(new_journal.amount.amount, Decimal('-5'))

        # mastercheck to see if Donation and related Journals addup
        self._check_if_journal_total_equals_value(new_journal, Decimal('145'))

        # Change the donation without changing the amount, no journal should be created.
        donation_from_db = self._get_only_one_from_db(Donation)
        self.assertEqual(DonationJournal.objects.all().count(), 3)
        donation_from_db.completed = timezone.now()
        donation_from_db.save()
        self.assertEqual(DonationJournal.objects.all().count(), 3)

    def test_journal_created_when_project_project_payout_is_made(self):
        """
        same as test_journal_created_when_donation_is_made, only
        with a ProjectPayout instead of a Donation.
        """
        self.assertEqual(ProjectPayoutJournal.objects.all().count(), 0)
        self.assertEqual(ProjectPayout.objects.count(), 0)
        self.payout = ProjectPayoutFactory.create(project=self.project,
                                                  amount_raised=Decimal('110'),
                                                  organization_fee=Decimal('10'),
                                                  amount_payable=Decimal('100'),
                                                  )

        # creation of a payout should always result in the creation of a journal
        payout_from_db = self._get_only_one_from_db(ProjectPayout)
        journal_from_db = self._get_only_one_from_db(ProjectPayoutJournal)

        self.assertEqual(journal_from_db.payout, payout_from_db)
        self.assertEqual(journal_from_db.amount.amount, Decimal('100'))

        # #### Create a Journal, check if it results in an updated Payout ##### #
        journal = ProjectPayoutJournal.objects.create(payout=self.payout,
                                                      amount=Money(50, 'EUR'))
        new_journal_pk = journal.pk
        self.assertEqual(ProjectPayoutJournal.objects.all().count(), 2)
        new_journal_from_db = ProjectPayoutJournal.objects.get(pk=new_journal_pk)

        self.assertEqual(new_journal_from_db.user_reference, '')  # should be auto filled with donation user
        self.assertEqual(new_journal_from_db.description, '')  # should be blank

        self.assertEqual(new_journal_from_db.date.date(), date.today())  # date today

        # the payout should be updated with the amount added via the journal
        payout_from_db = self._get_only_one_from_db(ProjectPayout)
        self.assertEqual(payout_from_db.amount_payable, Decimal('150'))  # change to new amount

        self._check_if_journal_total_equals_value(new_journal_from_db, payout_from_db.amount_payable)

        # Change the payout, and check if a new Journal is created
        payout_from_db.amount_payable = Decimal('145')
        payout_from_db.save()
        self.assertEqual(ProjectPayoutJournal.objects.all().count(), 3)
        new_journal = ProjectPayoutJournal.objects.all()[2]  # the latest is the newest
        self.assertEqual(new_journal.amount.amount, Decimal('-5'))

        # mastercheck to see if payout and related Journals addup
        self._check_if_journal_total_equals_value(new_journal, Decimal('145'))

        # Change the payout without changing the amount, no journal should be created.
        payout_from_db = self._get_only_one_from_db(ProjectPayout)
        self.assertEqual(ProjectPayoutJournal.objects.all().count(), 3)
        payout_from_db.sender_account_number = 'some number'
        payout_from_db.save()
        self.assertEqual(ProjectPayoutJournal.objects.all().count(), 3)
