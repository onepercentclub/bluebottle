from mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from bluebottle.members.models import CustomMemberField, CustomMemberFieldSettings, MemberPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import LocationFactory
from bluebottle.segments.tests.factories import SegmentFactory, SegmentTypeFactory
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
        """
        When the user is successfully authenticated,
        a new user should be created
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
        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertTrue(created)
            self.assertEqual(user.email, 'test@example.com')

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com',
            'email': 'test@example.com',
            'segment.team': 'Online Marketing',
            'segment.unit': 'Marketing',
        }
    )
    def test_user_created_segments(self, authenticate_request):
        team = SegmentTypeFactory.create(name='Team')
        team_segment = SegmentFactory.create(name='Online Marketing', type=team)
        SegmentFactory.create(name='Direct Marketing', type=team)

        unit = SegmentTypeFactory.create(name='Unit')
        unit_segment = SegmentFactory.create(name='Marketing', type=unit)
        SegmentFactory.create(name='Communications', type=unit)

        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertTrue(created)
            self.assertEqual(user.email, 'test@example.com')
            self.assertTrue(
                team_segment in user.segments.all()
            )
            self.assertTrue(
                unit_segment in user.segments.all()
            )

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com',
            'email': 'test@example.com',
            'segment.team': 'Marketing, online',
            'segment.unit': 'Marketing',
        }
    )
    def test_user_created_segments_alternative_name(self, authenticate_request):
        team = SegmentTypeFactory.create(name='Team')
        team_segment = SegmentFactory.create(
            name='Online Marketing',
            type=team,
            alternate_names=['Marketing, online']
        )
        SegmentFactory.create(name='Direct Marketing', type=team)

        unit = SegmentTypeFactory.create(name='Unit')
        unit_segment = SegmentFactory.create(name='Marketing', type=unit)
        SegmentFactory.create(name='Communications', type=unit)

        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertTrue(created)
            self.assertEqual(user.email, 'test@example.com')
            self.assertTrue(
                team_segment in user.segments.all()
            )
            self.assertTrue(
                unit_segment in user.segments.all()
            )

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com',
            'email': 'test@example.com',
            'segment.team': ['Marketing', 'Online Marketing'],
        }
    )
    def test_user_created_segments_list(self, authenticate_request):
        team = SegmentTypeFactory.create(name='Team')
        team_segment = SegmentFactory.create(
            name='Online Marketing',
            type=team,
        )
        SegmentFactory.create(name='Direct Marketing', type=team)

        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertTrue(created)
            self.assertEqual(user.email, 'test@example.com')
            self.assertTrue(
                team_segment in user.segments.all()
            )

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com',
            'email': 'test@example.com',
            'segment.team': ['Engineering', 'Software Engineering'],
        }
    )
    def test_user_created_segments_list_no_match(self, authenticate_request):
        member_settings = MemberPlatformSettings.load()
        member_settings.create_segments = False
        member_settings.save()
        team = SegmentTypeFactory.create(name='Team')
        SegmentFactory.create(
            name='Online Marketing',
            type=team,
        )
        SegmentFactory.create(name='Direct Marketing', type=team)

        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertTrue(created)
            self.assertEqual(user.email, 'test@example.com')
            self.assertEqual(len(user.segments.all()), 0)

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com',
            'email': 'test@example.com',
            'segment.team': ['Online Marketing'],
        }
    )
    def test_user_created_segments_list_no_match_create(self, authenticate_request):
        member_settings = MemberPlatformSettings.load()
        member_settings.create_segments = True
        member_settings.save()
        SegmentTypeFactory.create(name='Team')

        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertTrue(created)
            self.assertEqual(user.email, 'test@example.com')
            self.assertEqual(len(user.segments.all()), 1)
            self.assertEqual(user.segments.first().name, 'Online Marketing')
            self.assertEqual(user.segments.first().alternate_names, ['Online Marketing'])

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com',
            'email': 'test@example.com',
            'segment.team': 'Online Marketing',
            'segment.unit': 'Marketing',
        }
    )
    def test_user_updated_segments(self, authenticate_request):
        user = BlueBottleUserFactory.create(remote_id='test@example.com')
        team = SegmentTypeFactory.create(name='Team')
        team_segment = SegmentFactory.create(name='Online Marketing', type=team)
        user.segments.add(
            SegmentFactory.create(name='Direct Marketing', type=team)
        )

        unit = SegmentTypeFactory.create(name='Unit')
        unit_segment = SegmentFactory.create(name='Marketing', type=unit)
        user.segments.add(
            SegmentFactory.create(name='Communications', type=unit)
        )

        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertFalse(created)
            self.assertEqual(user.email, 'test@example.com')
            self.assertEqual(len(user.segments.all()), 2)
            self.assertTrue(
                team_segment in user.segments.all()
            )
            self.assertTrue(
                unit_segment in user.segments.all()
            )

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com',
            'email': 'test@example.com',
            'segment.team': 'Other Marketing',
            'segment.unit': 'Engineering',
        }
    )
    def test_user_created_segments_missing(self, authenticate_request):
        BlueBottleUserFactory.create(remote_id='test@example.com')
        team = SegmentTypeFactory.create(name='Team')
        SegmentFactory.create(name='Online Marketing', type=team)
        SegmentFactory.create(name='Direct Marketing', type=team)

        unit = SegmentTypeFactory.create(name='Unit')
        SegmentFactory.create(name='Marketing', type=unit)
        SegmentFactory.create(name='Communications', type=unit)

        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertFalse(created)
            self.assertEqual(user.email, 'test@example.com')
            self.assertEqual(len(user.segments.all()), 0)

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com',
            'email': 'test@example.com',
            'segment.team': 'Other Marketing',
            'segment.unit': 'Engineering',
        }
    )
    def test_user_created_segments_missing_create(self, authenticate_request):
        member_settings = MemberPlatformSettings.load()
        member_settings.create_segments = True
        member_settings.save()
        SegmentTypeFactory.create(name='Team')
        SegmentTypeFactory.create(name='Unit')

        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()
            self.assertEqual(user.email, 'test@example.com')
            self.assertEqual(len(user.segments.all()), 2)

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
