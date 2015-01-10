from bluebottle.test.utils import BluebottleTestCase
from django.utils import timezone
from django.core import mail

from mock import patch

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.utils.model_dispatcher import get_taskmember_model
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.projects import ProjectPhaseFactory, ProjectFactory
from bluebottle.test.factory_models.fundraisers import FundraiserFactory

TASKS_MEMBER_MODEL = get_taskmember_model()


class BlueBottleUserManagerTestCase(BluebottleTestCase):
    """
    Test case for the model manager of the abstract user model.
    """
    def test_create_user(self):
        """
        Tests the manager ``create_user`` method.
        """
        user = BlueBottleUserFactory.objects.create_user(email='john_doe@onepercentclub.com')

        self.assertEqual(user.username, 'john_doe')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_create_user_no_email_provided(self):
        """
        Tests exception raising when trying to create a new user without
        providing an email.
        """
        self.assertRaisesMessage(
            ValueError,
            'The given email address must be set',
            BlueBottleUserFactory.objects.create_user,
            email='')


class BlueBottleUserTestCase(BluebottleTestCase):
    """
    Test case for the implementation of the abstract user model.
    """
    def setUp(self):
        self.user = BlueBottleUserFactory.create()

    @patch('django.utils.timezone.now')
    def test_update_deleted_timestamp(self, mock):
        """
        Tests the ``update_deleted_timestamp`` method, checking that the
        timestamp is properly set up when the user is not active any more.
        """
        timestamp = timezone.now()
        mock.return_value = timestamp

        self.user.is_active = False
        self.user.update_deleted_timestamp()

        self.assertEqual(self.user.deleted, timestamp)

    def test_update_deleted_timestamp_active_user(self):
        """
        Tests that the ``update_deleted_timestamp`` method resets the timestamp
        to ``None`` if the user becomes active again.
        """
        self.user.is_active = False
        self.user.update_deleted_timestamp()

        # Now the user is inactive, so ``deleted`` attribute is set. Let's
        # reactivate it again and check that is reset.
        self.user.is_active = True
        self.user.update_deleted_timestamp()

        self.assertIsNone(self.user.deleted)

    def test_generate_username_from_email(self):
        """
        Tests the ``generate_username`` method when no username was provided.
        It should create the username from the name of the user email.
        """
        user = BlueBottleUserFactory.create(username='', first_name='', last_name='')
        user.generate_username()

        email_name, domain_part = user.email.strip().rsplit('@', 1)

        self.assertEqual(user.username, email_name)

    def test_generate_username_from_names(self):
        """
        Tests the ``generate_username`` method when no username was provided
        but ``first_name`` and ``last_name`` are defined.
        """
        user = BlueBottleUserFactory.create(username='', first_name=u'John', last_name=u'Doe')
        user.generate_username()

        self.assertEqual(user.username, 'johndoe')

    def test_get_full_name(self):
        """
        Tests the ``get_full_name`` method.
        """
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.user.save()

        self.assertEqual(self.user.get_full_name(), 'John Doe')

    def test_get_short_name(self):
        """
        Tests the ``get_short_name`` method.
        """
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.user.save()

        self.assertEqual(self.user.get_short_name(), 'John')

    def test_welcome_mail(self):
        """
        Test that a welcome mail is sent when a user is created when the setting are enabled
        In settings SEND_WELCOME_MAIL is set to False
        """
        from django.conf import settings
        settings.SEND_WELCOME_MAIL = True

        mail.outbox = []

        self.assertEqual(len(mail.outbox), 0)
        new_user = BlueBottleUserFactory.objects.create_user(email='new_user@onepercentclub.com')
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue("Welcome" in mail.outbox[0].subject) #We need a better way to verify the right mail is loaded
        self.assertEqual(mail.outbox[0].recipients()[0], new_user.email)

        settings.SEND_WELCOME_MAIL = False

    def test_no_welcome_mail(self):
        """
        Test that a welcome mail is sent when a user is created when the setting are disabled (= default)
        """
        mail.outbox = []

        self.assertEqual(len(mail.outbox), 0) #The setup function also creates a user and generates a mail
        new_user = BlueBottleUserFactory.objects.create_user(email='new_user@onepercentclub.com')
        self.assertEqual(len(mail.outbox), 0)

    def test_calculate_task_count(self):
        """ 
        Test that the task_count property on a user is calculated correctly. We count a) tasks where a user is a task author and 
        b) TaskMembers where a user is applied, accepted or realized
        """
        self.init_projects()

        self.assertEqual(self.user.task_count, 0)

        task = TaskFactory.create(author=self.user)
        self.assertEqual(self.user.task_count, 1)

        taskmember = TaskMemberFactory.create(
            member=self.user,
            status=TASKS_MEMBER_MODEL.TaskMemberStatuses.applied,
            task=task
        )

        self.assertEqual(self.user.task_count, 2)

        uncounted_taskmember = TaskMemberFactory.create(
            member=self.user,
            status=TASKS_MEMBER_MODEL.TaskMemberStatuses.stopped,
            task=task
        )

        self.assertEqual(self.user.task_count, 2)

    def test_calculate_donation_count(self):
        """ Test the counter for the number of donations a user has done """ 
        self.init_projects()

        self.assertEqual(self.user.donation_count, 0)

        order = OrderFactory.create(user=self.user)
        donation = DonationFactory.create(amount=1000, order=order)

        self.assertEqual(self.user.donation_count, 1)


    def test_calculate_project_count(self):
        """ Test the counter for the number of projects a user has started """
        self.init_projects()

        self.assertEqual(self.user.project_count, 0)

        project = ProjectFactory.create(owner=self.user)

        self.assertEqual(self.user.project_count, 1)

        project2 = ProjectFactory.create(owner=self.user)

        self.assertEqual(self.user.project_count, 2)

    def test_calculate_fundraiser_count(self):
        """ Test the counter for the number of fundraisers a user is owner of """
        self.init_projects()

        self.assertEqual(self.user.fundraiser_count, 0)

        fundraiser = FundraiserFactory.create(amount=4000, owner=self.user)

        self.assertEqual(self.user.fundraiser_count, 1)        
        
        fundraiser2 = FundraiserFactory.create(amount=4000, owner=self.user)

        self.assertEqual(self.user.fundraiser_count, 2)

