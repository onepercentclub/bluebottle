from mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from bluebottle.members.models import CustomMemberField, CustomMemberFieldSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import LocationFactory
from bluebottle.token_auth.auth.base import BaseTokenAuthentication


class TestBaseTokenAuthentication(TestCase):
    """
    Tests the Base Token Authentication backend.
    """
    def setUp(self):
        with self.settings(TOKEN_AUTH={}):
            self.auth = BaseTokenAuthentication(None)

    @patch.object(
        BaseTokenAuthentication, 'authenticate_request', return_value={'remote_id': 'test@example.com',
                                                                       'email': 'test@example.com'}
    )
    def test_user_created(self, authenticate_request):
        """ When the user is succesfully authenticated, a new user should
        be created
        """
        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertTrue(created)
            self.assertEqual(user.email, 'test@example.com')

    @patch.object(
        BaseTokenAuthentication, 'authenticate_request', return_value={'remote_id': 'test@example.com',
                                                                       'email': 'test@example.com',
                                                                       'custom.department': 'legal'
                                                                       }
    )
    def test_user_created_custom_field(self, authenticate_request):
        """ When the user is succesfully authenticated, a new user should
        be created
        """
        field = CustomMemberFieldSettings.objects.create(name='department')
        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertTrue(created)
            self.assertEqual(user.email, 'test@example.com')
            self.assertEqual(
                user.extra.get(field=field).value,
                'legal'
            )

    @patch.object(
        BaseTokenAuthentication, 'authenticate_request', return_value={'remote_id': 'test@example.com',
                                                                       'email': 'test@example.com',
                                                                       'custom.department': 'legal'
                                                                       }
    )
    def test_user_created_custom_field_missing_field(self, authenticate_request):
        """ When the user is succesfully authenticated, a new user should
        be created
        """
        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertTrue(created)
            self.assertEqual(user.email, 'test@example.com')

    @patch.object(
        BaseTokenAuthentication, 'authenticate_request', return_value={'remote_id': 'test@example.com',
                                                                       'email': 'test@example.com',
                                                                       'custom.department': 'legal'
                                                                       }
    )
    def test_user_created_custom_field_update(self, authenticate_request):
        """ When the user is succesfully authenticated, a new user should
        be created
        """
        user = BlueBottleUserFactory.create(remote_id='test@example.com')
        field = CustomMemberFieldSettings.objects.create(name='department')
        CustomMemberField.objects.create(field=field, member=user, value='finance')

        self.assertEqual(
            user.extra.get(field=field).value,
            'finance'
        )

        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertFalse(created)
            self.assertEqual(user.email, 'test@example.com')

            self.assertEqual(
                user.extra.get(field=field).value,
                'legal'
            )

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com',
            'email': 'test@example.com',
            'location.slug': 'AMS'
        }
    )
    def test_user_created_location(self, authenticate_request):
        """ When the user is succesfully authenticated, a new user should
        be created
        """
        location = LocationFactory.create(name='Amsterdam', slug='AMS')
        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertTrue(created)

            user.refresh_from_db()

            self.assertEqual(user.email, 'test@example.com')
            self.assertEqual(user.location, location)

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com',
            'email': 'test@example.com',
            'location.slug': 'AMS'
        }
    )
    def test_user_created_location_missing(self, authenticate_request):
        """ When the user is succesfully authenticated, a new user should
        be created
        """
        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertTrue(created)
            self.assertEqual(user.email, 'test@example.com')

    @patch.object(
        BaseTokenAuthentication, 'authenticate_request', return_value={'remote_id': 'test@example.com',
                                                                       'email': 'test@example.com'}
    )
    def test_user_already_exists(self, authenticate_request):
        with self.settings(TOKEN_AUTH={}):
            get_user_model()(remote_id='test@example.com', email='test@example.com').save()

            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertFalse(created)
            self.assertEqual(user.email, 'test@example.com')

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={'remote_id': 'test@example.com'}
    )
    def test_user_already_exists_only_remote_id(self, authenticate_request):
        with self.settings(TOKEN_AUTH={}):
            get_user_model()(remote_id='test@example.com', email='test@example.com').save()

            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertFalse(created)
            self.assertEqual(user.email, 'test@example.com')

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com',
            'email': 'test@example.com'
        }
    )
    def test_user_already_exists_without_remote_id(self, authenticate_request):
        with self.settings(TOKEN_AUTH={}):
            get_user_model()(email='test@example.com').save()

            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertFalse(created)
            self.assertEqual(user.email, 'test@example.com')
            self.assertEqual(user.remote_id, 'test@example.com')

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com'
        }
    )
    def test_user_new_only_remote_id(self, authenticate_request):
        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertTrue(created)
            self.assertEqual(user.remote_id, 'test@example.com')

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={'remote_id': 'test@example.com', 'email': 'test@example.com', 'first_name': 'updated'}
    )
    def test_user_already_exists_attributes_updated(self, authenticate_request):
        with self.settings(TOKEN_AUTH={}):
            get_user_model()(remote_id='test@example.com', email='test@example.com', first_name='test').save()

            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertFalse(created)
            self.assertEqual(user.email, 'test@example.com')
            self.assertEqual(user.first_name, 'updated')
