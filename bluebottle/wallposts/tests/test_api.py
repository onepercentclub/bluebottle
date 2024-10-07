from builtins import str
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from djmoney.money import Money
from rest_framework import status

from bluebottle.time_based.tests.factories import DateActivityFactory, PeriodActivityFactory
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.wallposts import (
    TextWallpostFactory, MediaWallpostFactory, MediaWallpostPhotoFactory
)
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.tests.test_unit import UserTestsMixin


class WallpostPermissionsTest(UserTestsMixin, BluebottleTestCase):
    def setUp(self):
        super(WallpostPermissionsTest, self).setUp()

        self.owner = BlueBottleUserFactory.create()
        self.owner_token = "JWT {0}".format(self.owner.get_jwt_token())
        self.manager = BlueBottleUserFactory.create()

        self.initiative = InitiativeFactory.create(
            owner=self.owner,
            activity_managers=[
                self.manager
            ]
        )
        self.activity = DateActivityFactory.create(
            owner=self.owner,
            initiative=self.initiative
        )
        self.on_a_data_activity = DateActivityFactory.create(
            owner=self.owner,
            initiative=self.initiative
        )
        self.period_activity = PeriodActivityFactory.create(
            owner=self.owner,
            initiative=self.initiative
        )

        self.other_user = BlueBottleUserFactory.create()
        self.other_token = "JWT {0}".format(
            self.other_user.get_jwt_token())

        self.media_wallpost_url = reverse('media_wallpost_list')
        self.text_wallpost_url = reverse('text_wallpost_list')
        self.wallpost_url = reverse('wallpost_list')

    def test_permissions_on_initiative_wallpost_sharing(self):
        """
        Tests that only the initiative creator can share a wallpost.
        """
        wallpost_data = {'parent_id': self.initiative.id,
                         'parent_type': 'initiative',
                         'text': 'I can share stuff!',
                         'email_followers': True}

        # The owner can share a wallpost
        response = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.owner_token)

        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED,
            'Initiative promoters can share a wallpost.')

        self.initiative.promoter = BlueBottleUserFactory.create()
        self.initiative.save()
        promoter_token = "JWT {0}".format(self.initiative.promoter.get_jwt_token())

        response = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=promoter_token)

        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED,
            'Initiative promoters can share a wallpost.')

        # Non-owner users can't share a post
        response = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.other_token)

        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN,
            'Random user can nog share wallpost.'
        )

        # Activity managers can share a post
        manager_token = "JWT {0}".format(self.manager.get_jwt_token())
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=manager_token)

        self.assertEqual(wallpost.status_code,
                         status.HTTP_201_CREATED)

    def test_permissions_on_period_activity_wallpost_sharing(self):
        """
        Tests that only the period activity creator can share a wallpost.
        """
        wallpost_data = {'parent_id': str(self.period_activity.id),
                         'parent_type': 'period',
                         'text': 'I can share stuff!',
                         'email_followers': True}

        # Non-owner users can't share a post
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.other_token)

        self.assertEqual(wallpost.status_code, status.HTTP_403_FORBIDDEN)

        self.period_activity.initiative.promoter = BlueBottleUserFactory.create()
        self.period_activity.initiative.save()
        promoter_token = "JWT {0}".format(self.period_activity.initiative.promoter.get_jwt_token())

        # Period activity owner can share a post
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=promoter_token)

        self.assertEqual(wallpost.status_code,
                         status.HTTP_201_CREATED)

        # Promoters users can share a post
        promoter_token = "JWT {0}".format(self.period_activity.initiative.promoter.get_jwt_token())
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=promoter_token)

        self.assertEqual(wallpost.status_code,
                         status.HTTP_201_CREATED)

        # Activity managers can share a post
        manager_token = "JWT {0}".format(self.manager.get_jwt_token())
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=manager_token)

        self.assertEqual(wallpost.status_code,
                         status.HTTP_201_CREATED)

    def test_permissions_on_period_activity_wallpost_non_sharing(self):
        """
        Tests other can post, without sharing
        """
        wallpost_data = {'parent_id': str(self.period_activity.id),
                         'parent_type': 'period',
                         'email_followers': False,
                         'text': 'I can share stuff!'}

        # Non-owner users can post, without email followers
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.other_token)

        self.assertEqual(wallpost.status_code, status.HTTP_201_CREATED)

    def test_permissions_on_date_acivity_wallpost_sharing(self):
        """
        Tests that only the date activity creator can share a wallpost.
        """
        wallpost_data = {'parent_id': str(self.activity.id),
                         'parent_type': 'date',
                         'text': 'I can share stuff!',
                         'share_with_facebook': True}

        # Non-owner users can't share a post
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.other_token)
        self.assertEqual(wallpost.status_code, status.HTTP_403_FORBIDDEN)

    def test_permissions_on_on_a_date_wallpost_sharing(self):
        """
        Tests that only the date activity creator can share a wallpost.
        """
        wallpost_data = {'parent_id': str(self.on_a_data_activity.id),
                         'parent_type': 'date',
                         'text': 'I can share stuff!',
                         'share_with_facebook': True}

        # Non-owner users can't share a post
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.other_token)
        self.assertEqual(wallpost.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_on_period_activity_wallpost_list(self):
        self.initiative.activity_manager = BlueBottleUserFactory.create()
        self.initiative.promoter = BlueBottleUserFactory.create()
        self.initiative.save()

        authenticated = Group.objects.get(name='Authenticated')

        authenticated.permissions.remove(
            Permission.objects.get(codename='api_read_wallpost')
        )
        authenticated.permissions.add(
            Permission.objects.get(codename='api_read_own_wallpost')
        )

        MediaWallpostFactory.create_batch(3, content_object=self.initiative)

        response = self.client.get(
            self.wallpost_url,
            {'parent_id': self.initiative.id, 'parent_type': 'initiative'},
            token=self.owner_token
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)


class WallpostRateLimitTestCase(UserTestsMixin, BluebottleTestCase):
    def setUp(self):
        super(WallpostRateLimitTestCase, self).setUp()

        self.owner = BlueBottleUserFactory.create(password='testing', first_name='someName', last_name='someLast')
        self.owner_token = "JWT {0}".format(self.owner.get_jwt_token())

        self.initiative = InitiativeFactory.create(owner=self.owner)
        self.activity = DateActivityFactory.create(owner=self.owner)
        self.media_wallpost_url = reverse('media_wallpost_list')

    def test_rate_limit_sharing(self):
        """
        Tests that only 10 wallpost are possible in succession.
        """
        wallpost_data = {
            'parent_id': self.initiative.id,
            'parent_type': 'initiative',
            'text': 'I can share stuff!',
            'email_followers': True
        }

        for i in range(10):
            response = self.client.post(
                self.media_wallpost_url,
                wallpost_data,
                token=self.owner_token
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            self.media_wallpost_url,
            wallpost_data,
            token=self.owner_token
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_rate_limit_no_sharing(self):
        """
        Tests that more then 10 wallposts are possible if wallpost is not shared
        """
        wallpost_data = {
            'parent_id': self.initiative.id,
            'parent_type': 'initiative',
            'text': 'I can share stuff!',
            'email_followers': False
        }

        for i in range(10):
            response = self.client.post(
                self.media_wallpost_url,
                wallpost_data,
                token=self.owner_token
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            self.media_wallpost_url,
            wallpost_data,
            token=self.owner_token
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class WallpostDeletePermissionTest(BluebottleTestCase):
    def setUp(self):
        super(WallpostDeletePermissionTest, self).setUp()

        self.owner = BlueBottleUserFactory.create()
        self.owner_token = "JWT {0}".format(self.owner.get_jwt_token())

        self.author_user = BlueBottleUserFactory.create()
        self.author_token = "JWT {0}".format(
            self.author_user.get_jwt_token())

        self.other_user = BlueBottleUserFactory.create()
        self.other_token = "JWT {0}".format(
            self.other_user.get_jwt_token())

        self.initiative = InitiativeFactory.create(owner=self.owner)

        self.wallpost = MediaWallpostFactory.create(
            content_object=self.initiative,
            author=self.author_user
        )

        self.wallpost_detail_url = reverse('wallpost_detail', args=(self.wallpost.id, ))

    def test_delete_own_wallpost(self):
        response = self.client.delete(
            self.wallpost_detail_url,
            token=self.author_token
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_other_wallpost(self):
        response = self.client.delete(
            self.wallpost_detail_url,
            token=self.other_token
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_wallpost_activity_owner(self):
        response = self.client.delete(
            self.wallpost_detail_url,
            token=self.owner_token
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_wallpost_no_authorization(self):
        response = self.client.delete(
            self.wallpost_detail_url
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WallpostReactionApiIntegrationTest(BluebottleTestCase):
    """
    Integration tests for the Initiative Media Wallpost API.
    """

    def setUp(self):
        super(WallpostReactionApiIntegrationTest, self).setUp()

        self.manager = BlueBottleUserFactory.create()
        self.manager_token = "JWT {0}".format(
            self.manager.get_jwt_token())
        self.activity = DateActivityFactory.create(owner=self.manager)
        self.some_wallpost = TextWallpostFactory.create(content_object=self.activity)
        self.another_wallpost = TextWallpostFactory.create()

        self.some_user = BlueBottleUserFactory.create(
            password='testing', first_name='someName', last_name='someLast')
        self.some_token = "JWT {0}".format(self.some_user.get_jwt_token())

        self.another_user = BlueBottleUserFactory.create(
            password='testing2', first_name='anotherName',
            last_name='anotherLast')
        self.another_token = "JWT {0}".format(
            self.another_user.get_jwt_token())

        self.wallpost_reaction_url = reverse('wallpost_reaction_list')
        self.wallpost_url = reverse('wallpost_list')
        self.text_wallpost_url = reverse('text_wallpost_list')

        response = self.client.post(
            self.wallpost_reaction_url,
            {
                'text': 'Dit is een test',
                'wallpost': self.some_wallpost.id
            },
            token=self.some_token
        )
        self.reaction_detail_url = reverse('wallpost_reaction_detail', kwargs={'pk': response.data['id']})

    def test_wallpost_reaction_create(self):
        reaction_text = "Hear! Hear!"
        response = self.client.post(self.wallpost_reaction_url,
                                    {'text': reaction_text,
                                     'wallpost': self.some_wallpost.id},
                                    token=self.some_token)

        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(reaction_text in response.data['text'])

    def test_wallpost_reaction_retrieve(self):
        response = self.client.get(self.reaction_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue('Dit is een test' in response.data['text'])

    def test_wallpost_reaction_update(self):
        new_reaction_text = 'HEAR!!! HEAR!!!'
        response = self.client.put(
            self.reaction_detail_url,
            {
                'text': new_reaction_text,
                'wallpost': self.some_wallpost.id
            },
            token=self.some_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(new_reaction_text in response.data['text'])

    def test_wallpost_reaction_retrieve_other_user(self):
        response = self.client.get(self.reaction_detail_url, token=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue('Dit is een test' in response.data['text'])

    def test_wallpost_reaction_delete(self):
        response = self.client.delete(self.reaction_detail_url, token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_wallpost_reaction_delete_another_user(self):
        response = self.client.delete(self.reaction_detail_url, token=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wallpost_reaction_delete_wall_owner(self):
        response = self.client.delete(self.reaction_detail_url, token=self.manager_token)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_wallpost_reaction_delete_then_retrieve(self):
        response = self.client.delete(self.reaction_detail_url, token=self.some_token)
        response = self.client.get(self.reaction_detail_url, token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)

    def test_reactions_on_multiple_objects(self):
        """
        Tests for multiple reactions and unauthorized reaction updates.
        """

        # Create two reactions.
        reaction_text_1 = 'Great job!'
        response = self.client.post(self.wallpost_reaction_url,
                                    {'text': reaction_text_1,
                                     'wallpost': self.some_wallpost.id},
                                    token=self.some_token)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(reaction_text_1 in response.data['text'])

        reaction_text_2 = 'This is a really nice post.'
        response = self.client.post(self.wallpost_reaction_url,
                                    {'text': reaction_text_2,
                                     'wallpost': self.some_wallpost.id},
                                    token=self.some_token)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(reaction_text_2 in response.data['text'])

        # Create a reaction on second blog post.
        reaction_text_3 = 'Super!'
        response = self.client.post(self.wallpost_reaction_url,
                                    {'text': reaction_text_3,
                                     'wallpost': self.another_wallpost.id},
                                    token=self.some_token)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(reaction_text_3 in response.data['text'])
        # Save the detail url to be used in the authorization test below.
        second_reaction_detail_url = reverse(
            'wallpost_reaction_detail', kwargs={'pk': response.data['id']})

        # Test that a reaction update from a user who is not the author is
        # forbidden.
        response = self.client.post(second_reaction_detail_url,
                                    {'text': 'Can I update this reaction?'},
                                    token=self.another_token)
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED,
            response.data)


class TestWallpostAPIPermissions(BluebottleTestCase):
    """
    API endpoint test where endpoint (wallpost) has explicit
    permission_classes, overriding the global default
    """

    def setUp(self):
        super(TestWallpostAPIPermissions, self).setUp()

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.some_initiative = InitiativeFactory.create(owner=self.user)
        self.some_wallpost = TextWallpostFactory.create(
            content_object=self.some_initiative,
            author=self.user)
        self.wallpost_url = reverse('wallpost_list')

    def test_closed_api_readonly_permission_noauth(self):
        """ an endpoint with an explicit *OrReadOnly permission
            should still be closed """
        anonymous = Group.objects.get(name='Anonymous')
        anonymous.permissions.remove(
            Permission.objects.get(codename='api_read_wallpost')
        )

        response = self.client.get(self.wallpost_url,
                                   {'parent_id': self.some_initiative.id,
                                    'parent_type': 'initiative'})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_open_api_readonly_permission_noauth(self):
        """ an endpoint with an explicit *OrReadOnly permission
            should still be closed """
        MemberPlatformSettings.objects.update(closed=True)
        response = self.client.get(self.wallpost_url,
                                   {'parent_id': self.some_initiative.id,
                                    'parent_type': 'initiative'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_closed_api_readonly_permission_auth(self):
        """ an endpoint with an explicit *OrReadOnly permission
            should still be closed """
        MemberPlatformSettings.objects.update(closed=False)
        response = self.client.get(self.wallpost_url,
                                   {'parent_id': self.some_initiative.id,
                                    'parent_type': 'initiative'},
                                   token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestPinnedWallpost(BluebottleTestCase):
    """
    Test that initiator wallposts get pinned and unpinned correctly.
    """

    def setUp(self):
        super(TestPinnedWallpost, self).setUp()

        self.initiator = BlueBottleUserFactory.create()
        self.initiator_token = "JWT {0}".format(self.initiator.get_jwt_token())

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.initiative = InitiativeFactory.create(owner=self.initiator)

        self.wallpost_url = reverse('wallpost_list')
        self.text_wallpost_url = reverse('text_wallpost_list')

    def test_pinned_wallposts(self):

        wallpost = MediaWallpostFactory.create(author=self.initiator, content_object=self.initiative)
        wallpost.refresh_from_db()
        self.assertEqual(wallpost.pinned, True)
        MediaWallpostFactory.create(author=self.user, content_object=self.initiative)
        MediaWallpostFactory.create(author=self.initiator, content_object=self.initiative)
        MediaWallpostFactory.create_batch(3, author=self.user, content_object=self.initiative)

        response = self.client.get(self.wallpost_url,
                                   {'parent_id': self.initiative.id, 'parent_type': 'initiative'},
                                   token=self.user_token)

        # There should be 6 wallposts
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 6)

        # First post should by latest by the initiator
        self.assertEqual(response.data['results'][0]['author']['id'], self.initiator.id)
        self.assertEqual(response.data['results'][0]['pinned'], True)

        # Second item shoudl be by user and unpinned
        self.assertEqual(response.data['results'][1]['author']['id'], self.user.id)
        self.assertEqual(response.data['results'][1]['pinned'], False)

        # The sixth wallposts should be by initiator but unpinned
        self.assertEqual(response.data['results'][5]['author']['id'], self.initiator.id)
        self.assertEqual(response.data['results'][5]['pinned'], False)


class InitiativeWallpostTest(BluebottleTestCase):
    def setUp(self):
        super(InitiativeWallpostTest, self).setUp()

        self.owner = BlueBottleUserFactory.create()
        self.owner_token = "JWT {0}".format(self.owner.get_jwt_token())

        self.initiative = InitiativeFactory.create(owner=self.owner)
        self.activity = DateActivityFactory.create(owner=self.owner)
        self.on_a_data_activity = DateActivityFactory.create(owner=self.owner)

        self.other_user = BlueBottleUserFactory.create()
        self.other_token = "JWT {0}".format(
            self.other_user.get_jwt_token())

        self.media_wallpost_url = reverse('media_wallpost_list')
        self.text_wallpost_url = reverse('text_wallpost_list')
        self.wallpost_url = reverse('wallpost_list')

    def test_create_initiative_wallpost(self):
        """
        Tests that only the initiative creator can share a wallpost.
        """
        wallpost_data = {'parent_id': self.initiative.id,
                         'parent_type': 'initiative',
                         'text': 'I can share stuff!',
                         'share_with_twitter': True}

        # The owner can share a wallpost
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.owner_token)

        self.assertEqual(
            wallpost.status_code, status.HTTP_201_CREATED,
            'Initiative owners can share a wallpost.')

        self.initiative.promoter = BlueBottleUserFactory.create()
        self.initiative.save()
        promoter_token = "JWT {0}".format(self.initiative.promoter.get_jwt_token())

        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=promoter_token)

        self.assertEqual(
            wallpost.status_code, status.HTTP_201_CREATED,
            'Initiative promoters can share a wallpost.')

        # Non-owner users can't share a post
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.other_token)

        self.assertEqual(wallpost.status_code, status.HTTP_403_FORBIDDEN)

    def test_get(self):
        self.test_create_initiative_wallpost()

        params = {'parent_id': self.initiative.id, 'parent_type': 'initiative'}
        response = self.client.get(self.wallpost_url, params)
        self.assertEqual(response.data['count'], 2)

        for wallpost in response.data['results']:
            self.assertIsNotNone(wallpost['author']['last_name'])

    def test_get_only_first_name(self):
        MemberPlatformSettings.objects.update_or_create(display_member_names='first_name')
        self.test_create_initiative_wallpost()

        params = {'parent_id': self.initiative.id, 'parent_type': 'initiative'}
        response = self.client.get(self.wallpost_url, params)

        for wallpost in response.data['results']:
            self.assertFalse('last_name' in wallpost['author'])
            self.assertEqual(wallpost['author']['full_name'], wallpost['author']['first_name'])

    def test_get_only_first_name_staff(self):
        MemberPlatformSettings.objects.update_or_create(display_member_names='first_name')
        self.test_create_initiative_wallpost()
        staff = BlueBottleUserFactory.create(is_staff=True)
        staff_token = "JWT {0}".format(staff.get_jwt_token())
        params = {'parent_id': self.initiative.id, 'parent_type': 'initiative'}
        response = self.client.get(
            self.wallpost_url, params, token=staff_token)

        for wallpost in response.data['results']:
            self.assertTrue('last_name' in wallpost['author'])
            self.assertEqual(
                wallpost['author']['full_name'],
                wallpost['author']['first_name'] + ' ' + wallpost['author']['last_name']
            )

    def test_create_on_a_date_wallpost(self):
        """
        Tests that only the date activity creator can share a wallpost.
        """
        wallpost_data = {'parent_id': self.on_a_data_activity.id,
                         'parent_type': 'date',
                         'text': 'I can share stuff!',
                         'share_with_twitter': True}

        # The owner can share a wallpost
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.owner_token)

        self.assertEqual(
            wallpost.status_code, status.HTTP_201_CREATED,
            'Date activity owners can share a wallpost.')

    def test_create_wallpost_empty_donation(self):
        """
        Tests that only the date activity creator can share a wallpost.
        """
        wallpost_data = {'parent_id': self.activity.id,
                         'parent_type': 'date',
                         'text': 'I can share stuff!',
                         'donation': None}

        # The owner can post with empty donation
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.owner_token)

        self.assertEqual(
            wallpost.status_code, status.HTTP_201_CREATED,
            'Date acitivity owners can post a wallpost with empty donation set.')

    def test_create_date_activity_wallpost_other(self):
        """
        Tests that only the date activity creator can share a wallpost.
        """
        wallpost_data = {'parent_id': self.activity.id,
                         'parent_type': 'date',
                         'text': 'I want to share stuff!',
                         'share_with_twitter': True}

        # Non-owner users can't share a post
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.other_token)

        self.assertEqual(wallpost.status_code, status.HTTP_403_FORBIDDEN)


class WallpostPhotoTest(BluebottleTestCase):
    def setUp(self):
        super(WallpostPhotoTest, self).setUp()

        self.owner = BlueBottleUserFactory.create()
        self.owner_token = "JWT {0}".format(self.owner.get_jwt_token())

        self.initiative = InitiativeFactory.create(owner=self.owner)
        self.funding = FundingFactory.create(target=Money(5000, 'EUR'), status='open', initiative=self.initiative)

        self.wallpost = MediaWallpostFactory.create(content_object=self.funding)

        self.photo = MediaWallpostPhotoFactory(
            author=self.wallpost.author,
            mediawallpost=MediaWallpostFactory.create(content_object=self.funding, author=self.wallpost.author)
        )

        self.url = reverse('mediawallpost_photo_detail', args=(self.photo.pk, ))

    def test_photo(self):
        response = self.client.put(
            self.url,
            data={
                'mediawallpost': self.wallpost.pk
            },
            token="JWT {0}".format(self.photo.author.get_jwt_token())
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('jpg' in response.data['photo']['full'])

    def test_photo_different_wallpost_owner(self):
        photo_author = BlueBottleUserFactory.create()
        self.photo.author = photo_author
        self.photo.mediawallpost = MediaWallpostFactory.create(content_object=self.funding, author=photo_author)
        self.photo.save()

        response = self.client.put(
            self.url,
            data={
                'mediawallpost': self.wallpost.pk
            },
            token="JWT {0}".format(self.photo.author.get_jwt_token())
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
