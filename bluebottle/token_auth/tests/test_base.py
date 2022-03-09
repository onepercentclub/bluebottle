from mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import LocationFactory
from bluebottle.segments.tests.factories import SegmentFactory, SegmentTypeFactory
from bluebottle.members.models import UserSegment
from bluebottle.token_auth.auth.base import BaseTokenAuthentication


class TestBaseTokenAuthentication(TestCase):
    """
    Tests the Base Token Authentication backend.
    """

    def setUp(self):
        with self.settings(TOKEN_AUTH={}):
            self.auth = BaseTokenAuthentication(None)

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com',
            'email': 'test@example.com'
        }
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
    def test_user_updated_location(self, authenticate_request):
        BlueBottleUserFactory.create(remote_id='test@example.com', location=None)

        location = LocationFactory.create(name='Amsterdam', slug='AMS')
        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertFalse(created)

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
    def test_user_updated_location_verified(self, authenticate_request):
        location = LocationFactory.create()
        BlueBottleUserFactory.create(
            remote_id='test@example.com',
            location=location,
            location_verified=True
        )

        LocationFactory.create(name='Amsterdam', slug='AMS')

        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertEqual(authenticate_request.call_count, 1)
            self.assertFalse(created)

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
        team_segment = SegmentFactory.create(name='Online Marketing', segment_type=team)
        SegmentFactory.create(name='Direct Marketing', segment_type=team, email_domains=[])

        unit = SegmentTypeFactory.create(name='Unit')
        unit_segment = SegmentFactory.create(name='Marketing', segment_type=unit)
        SegmentFactory.create(name='Communications', segment_type=unit, email_domains=[])

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
            self.assertFalse(
                UserSegment.objects.get(segment=team_segment, member=user).verified
            )
            self.assertFalse(
                UserSegment.objects.get(segment=unit_segment, member=user).verified
            )
            self.assertEqual(
                user.required,
                []
            )

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com',
            'email': 'test@example.com',
            'segment.team': 'Online Marketing',
        }
    )
    def test_user_created_segments_unverified(self, authenticate_request):
        team = SegmentTypeFactory.create(name='Team', needs_verification=True)
        team_segment = SegmentFactory.create(name='Online Marketing', segment_type=team, email_domains=[])
        other_segment = SegmentFactory.create(name='Direct Marketing', segment_type=team, email_domains=[])

        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertTrue(
                team_segment in user.segments.all()
            )
            self.assertTrue(
                other_segment not in user.segments.all()
            )
            self.assertFalse(UserSegment.objects.get(segment=team_segment, member=user).verified)

        user.segments.add(
            other_segment,
            through_defaults={'verified': False}
        )

        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertTrue(
                team_segment in user.segments.all()
            )
            self.assertTrue(
                other_segment not in user.segments.all()
            )
            self.assertFalse(UserSegment.objects.get(segment=team_segment, member=user).verified)

    @patch.object(
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com',
            'email': 'test@example.com',
            'segment.team': 'Online Marketing',
        }
    )
    def test_user_created_segments_unverified_twice(self, authenticate_request):
        team = SegmentTypeFactory.create(name='Team', needs_verification=True)
        team_segment = SegmentFactory.create(
            name='Online Marketing', segment_type=team, email_domains=[]
        )
        other_segment = SegmentFactory.create(name='Direct Marketing', segment_type=team, email_domains=[])

        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

        user.segments.clear()
        user.segments.add(
            other_segment,
            through_defaults={'verified': True}
        )

        with self.settings(TOKEN_AUTH={}):
            user, created = self.auth.authenticate()

            self.assertTrue(
                team_segment not in user.segments.all()
            )

            self.assertTrue(
                other_segment in user.segments.all()
            )
            self.assertTrue(UserSegment.objects.get(segment=other_segment, member=user).verified)

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
            segment_type=team,
            alternate_names=['Marketing, online']
        )
        SegmentFactory.create(name='Direct Marketing', segment_type=team, email_domains=[])

        unit = SegmentTypeFactory.create(name='Unit')
        unit_segment = SegmentFactory.create(name='Marketing', segment_type=unit)
        SegmentFactory.create(name='Communications', segment_type=unit)

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
            segment_type=team,
            email_domains=[]
        )
        SegmentFactory.create(
            name='Direct Marketing',
            segment_type=team,
            email_domains=[]
        )

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
            segment_type=team,
            email_domains=[]
        )
        SegmentFactory.create(name='Direct Marketing', segment_type=team)

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
        team_segment = SegmentFactory.create(name='Online Marketing', segment_type=team, email_domains=[])
        user.segments.add(
            SegmentFactory.create(name='Direct Marketing', segment_type=team)
        )

        unit = SegmentTypeFactory.create(name='Unit')
        unit_segment = SegmentFactory.create(name='Marketing', segment_type=unit)
        user.segments.add(
            SegmentFactory.create(name='Communications', segment_type=unit)
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
        SegmentFactory.create(name='Online Marketing', segment_type=team, email_domains=[])
        SegmentFactory.create(name='Direct Marketing', segment_type=team, email_domains=[])

        unit = SegmentTypeFactory.create(name='Unit')
        SegmentFactory.create(name='Marketing', segment_type=unit)
        SegmentFactory.create(name='Communications', segment_type=unit)

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
        BaseTokenAuthentication,
        'authenticate_request',
        return_value={
            'remote_id': 'test@example.com',
            'email': 'test@example.com'
        }
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
