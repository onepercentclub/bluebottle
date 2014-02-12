from django.test import TestCase

from bluebottle.bb_accounts.models import BlueBottleUser


class BlueBottleUserManagerTestCase(TestCase):
    """
    Test case for the model manager of the abstract user model.
    """
    def test_create_user(self):
        """
        Tests the manager ``create_user`` method.
        """
        user = BlueBottleUser.objects.create_user(email='john_doe@onepercentclub.com')

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
            BlueBottleUser.objects.create_user,
            email='')
