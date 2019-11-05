import mock
from django.contrib.auth.models import Group, Permission
from django.core.urlresolvers import reverse
from djmoney.money import Money
from rest_framework import status

from bluebottle.events.tests.factories import EventFactory
from bluebottle.funding.tests.factories import DonationFactory, FundingFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.fundraisers import FundraiserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.tasks import TaskFactory
from bluebottle.test.factory_models.wallposts import (
    TextWallpostFactory, MediaWallpostFactory
)
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.tests.test_unit import UserTestsMixin


class WallpostPermissionsTest(UserTestsMixin, BluebottleTestCase):
    def setUp(self):
        super(WallpostPermissionsTest, self).setUp()

        self.init_projects()

        self.owner = BlueBottleUserFactory.create(password='testing', first_name='someName', last_name='someLast')
        self.owner_token = "JWT {0}".format(self.owner.get_jwt_token())

        self.project = ProjectFactory.create(owner=self.owner)
        self.fundraiser = FundraiserFactory.create(owner=self.owner)
        self.task = TaskFactory.create(author=self.owner)

        self.other_user = BlueBottleUserFactory.create()
        self.other_token = "JWT {0}".format(
            self.other_user.get_jwt_token())

        self.media_wallpost_url = reverse('media_wallpost_list')
        self.text_wallpost_url = reverse('text_wallpost_list')
        self.wallpost_url = reverse('wallpost_list')

    def test_permissions_on_project_wallpost_sharing(self):
        """
        Tests that only the project creator can share a wallpost.
        """
        wallpost_data = {'parent_id': self.project.slug,
                         'parent_type': 'project',
                         'text': 'I can share stuff!',
                         'share_with_twitter': True}

        # The owner can share a wallpost
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.owner_token)

        self.assertEqual(
            wallpost.status_code, status.HTTP_201_CREATED,
            'Project owners can share a wallpost.')

        self.project.promoter = BlueBottleUserFactory.create()
        self.project.save()
        promoter_token = "JWT {0}".format(self.project.promoter.get_jwt_token())

        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=promoter_token)

        self.assertEqual(
            wallpost.status_code, status.HTTP_201_CREATED,
            'Project promoters can share a wallpost.')

        # Non-owner users can't share a post
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.other_token)

        self.assertEqual(wallpost.status_code, status.HTTP_403_FORBIDDEN)

    def test_permissions_on_task_wallpost_sharing(self):
        """
        Tests that only the task creator can share a wallpost.
        """
        wallpost_data = {'parent_id': str(self.task.id),
                         'parent_type': 'task',
                         'text': 'I can share stuff!',
                         'share_with_linkedin': True}

        # Non-owner users can't share a post
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.other_token)

        self.assertEqual(wallpost.status_code, status.HTTP_403_FORBIDDEN)

        self.task.project.promoter = BlueBottleUserFactory.create()
        self.task.project.save()
        promoter_token = "JWT {0}".format(self.task.project.promoter.get_jwt_token())

        # Promoters users can share a post
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=promoter_token)

        self.assertEqual(wallpost.status_code,
                         status.HTTP_201_CREATED)

    def test_permissions_on_task_wallpost_non_sharing(self):
        """
        Tests other can post, without sharing
        """
        wallpost_data = {'parent_id': str(self.task.id),
                         'parent_type': 'task',
                         'email_followers': False,
                         'text': 'I can share stuff!'}

        # Non-owner users can post, without email followers
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.other_token)

        self.assertEqual(wallpost.status_code, status.HTTP_201_CREATED)

    def test_permissions_on_fundraiser_wallpost_sharing(self):
        """
        Tests that only the fundraiser creator can share a wallpost.
        """
        wallpost_data = {'parent_id': str(self.fundraiser.id),
                         'parent_type': 'fundraiser',
                         'text': 'I can share stuff!',
                         'share_with_facebook': True}

        # Non-owner users can't share a post
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.other_token)

        self.assertEqual(wallpost.status_code, status.HTTP_403_FORBIDDEN)

    def test_filtering_on_wallpost_list(self):
        authenticated = Group.objects.get(name='Authenticated')
        authenticated.permissions.remove(
            Permission.objects.get(codename='api_read_mediawallpost')
        )
        authenticated.permissions.add(
            Permission.objects.get(codename='api_read_own_mediawallpost')
        )

        MediaWallpostFactory.create(content_object=self.task)
        MediaWallpostFactory.create(content_object=self.project)
        MediaWallpostFactory.create(content_object=self.fundraiser)
        MediaWallpostFactory.create(content_object=ProjectFactory(owner=self.other_user))

        response = self.client.get(
            self.media_wallpost_url, token=self.owner_token)
        self.assertEqual(response.data['count'], 3)

        response = self.client.get(
            self.media_wallpost_url, token=self.other_token)
        self.assertEqual(response.data['count'], 1)

    def test_filter_on_task_wallpost_list(self):
        """
        Tests that project initiator can post and view task wallposts
        """
        self.project.task_manager = BlueBottleUserFactory.create()
        self.project.promoter = BlueBottleUserFactory.create()
        self.project.save()

        authenticated = Group.objects.get(name='Authenticated')

        authenticated.permissions.remove(
            Permission.objects.get(codename='api_read_wallpost')
        )
        authenticated.permissions.add(
            Permission.objects.get(codename='api_read_own_wallpost')
        )

        MediaWallpostFactory.create_batch(3, content_object=self.task)

        response = self.client.get(self.wallpost_url,
                                   {'parent_id': str(self.task.id), 'parent_type': 'task'},
                                   token=self.owner_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)


class WallpostDeletePermissionTest(BluebottleTestCase):
    def setUp(self):
        super(WallpostDeletePermissionTest, self).setUp()

        self.init_projects()

        self.owner = BlueBottleUserFactory.create()
        self.owner_token = "JWT {0}".format(self.owner.get_jwt_token())

        self.other_user = BlueBottleUserFactory.create()
        self.other_token = "JWT {0}".format(
            self.other_user.get_jwt_token())

        self.project = ProjectFactory.create(owner=self.owner)

        self.wallpost = MediaWallpostFactory.create(
            content_object=self.project,
            author=self.other_user
        )

        self.wallpost_detail_url = reverse('wallpost_detail', args=(self.wallpost.id, ))

    def test_delete_own_wallpost(self):
        """
        Tests that project initiator can post and view task wallposts
        """
        response = self.client.delete(
            self.wallpost_detail_url,
            token=self.other_token
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_other_wallpost(self):
        """
        Tests that project initiator can post and view task wallposts
        """
        response = self.client.delete(
            self.wallpost_detail_url,
            token=self.owner_token
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_wallpost_no_authorization(self):
        """
        Tests that project initiator can post and view task wallposts
        """
        response = self.client.delete(
            self.wallpost_detail_url
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WallpostReactionApiIntegrationTest(BluebottleTestCase):
    """
    Integration tests for the Project Media Wallpost API.
    """

    def setUp(self):
        super(WallpostReactionApiIntegrationTest, self).setUp()

        self.init_projects()

        self.some_wallpost = TextWallpostFactory.create()
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

    def test_wallpost_reaction_crud(self):
        """
        Tests for creating, retrieving, updating and deleting a reaction to a Project Wallpost.
        """

        # Create a Reaction
        reaction_text = "Hear! Hear!"
        response = self.client.post(self.wallpost_reaction_url,
                                    {'text': reaction_text,
                                     'wallpost': self.some_wallpost.id},
                                    token=self.some_token)

        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(reaction_text in response.data['text'])

        # Retrieve the created Reaction
        reaction_detail_url = reverse(
            'wallpost_reaction_detail', kwargs={'pk': response.data['id']})
        response = self.client.get(reaction_detail_url)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(reaction_text in response.data['text'])

        # Update the created Reaction by author.
        new_reaction_text = 'HEAR!!! HEAR!!!'
        response = self.client.put(reaction_detail_url,
                                   {'text': new_reaction_text,
                                    'wallpost': self.some_wallpost.id},
                                   token=self.some_token)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(new_reaction_text in response.data['text'])

        # switch to another user
        self.client.logout()

        # Retrieve the created Reaction by non-author should work
        response = self.client.get(
            reaction_detail_url, token=self.another_token)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(new_reaction_text in response.data['text'])

        # Delete Reaction by non-author should not work
        self.client.logout()
        response = self.client.delete(
            reaction_detail_url, token=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Create a Reaction by another user
        another_reaction_text = "I'm not so sure..."
        response = self.client.post(self.wallpost_reaction_url,
                                    {'text': another_reaction_text,
                                     'wallpost': self.some_wallpost.id},
                                    token=self.another_token)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data)
        # Only check the substring because the single quote in "I'm" is escaped.
        # https://docs.djangoproject.com/en/dev/topics/templates/#automatic-html-escaping
        self.assertTrue('not so sure' in response.data['text'])

        # retrieve the list of Reactions for this Wallpost should return two
        response = self.client.get(self.wallpost_reaction_url,
                                   {'wallpost': self.some_wallpost.id},
                                   token=self.another_token)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 2)
        self.assertTrue(
            new_reaction_text in response.data['results'][0]['text'])

        # Only check the substring because the single quote in "I'm" is escaped.
        # https://docs.djangoproject.com/en/dev/topics/templates/#automatic-html-escaping
        self.assertTrue('not so sure' in response.data['results'][1]['text'])

        # Delete Reaction by author should work
        response = self.client.delete(
            reaction_detail_url, token=self.some_token)
        self.assertEqual(
            response.status_code, status.HTTP_204_NO_CONTENT, response)

        # Retrieve the deleted Reaction should fail
        response = self.client.get(
            reaction_detail_url, token=self.another_token)
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND, response.data)

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

        # Check the size of the reaction list is correct.
        response = self.client.get(self.wallpost_reaction_url,
                                   {'wallpost': self.some_wallpost.id},
                                   token=self.some_token)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 2)

        # Check that the reaction listing without a wallpost id is working.
        response = self.client.get(
            self.wallpost_reaction_url, token=self.some_token)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 2)

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

        # Check that the size and data in the first reaction list is correct.
        response = self.client.get(self.wallpost_reaction_url,
                                   {'wallpost': self.some_wallpost.id},
                                   token=self.some_token)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)

        # filter_fields seems to do not work...WHYYYYY
        self.assertEqual(response.data['count'], 2)

        self.assertTrue(reaction_text_1 in response.data['results'][0]['text'])
        self.assertTrue(reaction_text_2 in response.data['results'][1]['text'])

        # Check that the size and data in the second reaction list is correct.
        response = self.client.get(self.wallpost_reaction_url,
                                   {'wallpost': self.another_wallpost.id},
                                   token=self.some_token)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertTrue(reaction_text_3 in response.data['results'][0]['text'])

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

        self.init_projects()
        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.some_project = ProjectFactory.create(owner=self.user)
        self.some_wallpost = TextWallpostFactory.create(
            content_object=self.some_project,
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
                                   {'parent_id': self.some_project.slug,
                                    'parent_type': 'project'})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch('bluebottle.clients.properties.CLOSED_SITE', False)
    def test_open_api_readonly_permission_noauth(self):
        """ an endpoint with an explicit *OrReadOnly permission
            should still be closed """
        response = self.client.get(self.wallpost_url,
                                   {'parent_id': self.some_project.slug,
                                    'parent_type': 'project'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch('bluebottle.clients.properties.CLOSED_SITE', True)
    def test_closed_api_readonly_permission_auth(self):
        """ an endpoint with an explicit *OrReadOnly permission
            should still be closed """
        response = self.client.get(self.wallpost_url,
                                   {'parent_id': self.some_project.slug,
                                    'parent_type': 'project'},
                                   token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestDonationWallpost(BluebottleTestCase):
    """
    Test that a wallpost is created after making a donation and that
    the system wallposts is removed if we post a comment.
    """
    def setUp(self):
        super(TestDonationWallpost, self).setUp()

        self.init_projects()
        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.funding = FundingFactory.create(status='open')
        self.wallpost_url = reverse('wallpost_list')
        self.text_wallpost_url = reverse('text_wallpost_list')

        donation = DonationFactory.create(
            user=self.user,
            activity=self.funding,
            fundraiser=None
        )
        donation.transitions.succeed()
        donation.save()

        self.data = {
            "title": "",
            "text": "What a nice project!",
            "parent_id": self.funding.id,
            "parent_type": "funding",
            "donation": donation.id,
            "email_followers": False
        }

    def test_donation_wallposts(self):
        # Create a donation and set it to settled to trigger wallpost
        # There should be one system wallpost now
        response = self.client.get(
            self.wallpost_url,
            {
                'parent_id': self.funding.id,
                'parent_type': 'funding'
            },
            token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['type'], 'system')

        # Now create a text wallpost for this donation (user enters text in thank you modal)
        response = self.client.post(self.text_wallpost_url, self.data, token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # The funding should still have one wallpost, only the message last added
        response = self.client.get(
            self.wallpost_url,
            {'parent_id': self.funding.id, 'parent_type': 'funding'},
            token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['type'], 'text')
        self.assertEqual(response.data['results'][0]['text'], '<p>What a nice project!</p>')

    def test_donation_wallposts_other_user(self):
        other_user = BlueBottleUserFactory.create()
        other_user_token = "JWT {0}".format(other_user.get_jwt_token())
        response = self.client.post(self.text_wallpost_url, self.data, token=other_user_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_donation_wallposts_anonymous(self):
        response = self.client.post(self.text_wallpost_url, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_donation_wallposts_twice(self):
        self.client.post(self.text_wallpost_url, self.data, token=self.user_token)
        response = self.client.post(self.text_wallpost_url, self.data, token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestPinnedWallpost(BluebottleTestCase):
    """
    Test that initiator wallposts get pinned and unpinned correctly.
    """

    def setUp(self):
        super(TestPinnedWallpost, self).setUp()

        self.init_projects()
        self.initiator = BlueBottleUserFactory.create()
        self.initiator_token = "JWT {0}".format(self.initiator.get_jwt_token())

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.project = ProjectFactory.create(owner=self.initiator)

        self.wallpost_url = reverse('wallpost_list')
        self.text_wallpost_url = reverse('text_wallpost_list')

    def test_pinned_wallposts(self):

        wallpost = MediaWallpostFactory.create(author=self.initiator, content_object=self.project)
        wallpost.refresh_from_db()
        self.assertEqual(wallpost.pinned, True)
        MediaWallpostFactory.create(author=self.user, content_object=self.project)
        MediaWallpostFactory.create(author=self.initiator, content_object=self.project)
        MediaWallpostFactory.create_batch(3, author=self.user, content_object=self.project)

        response = self.client.get(self.wallpost_url,
                                   {'parent_id': self.project.slug, 'parent_type': 'project'},
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
        self.event = EventFactory.create(owner=self.owner)

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

        params = {'parent_id': self.initiative.id, 'parent_type': 'initiative'}
        response = self.client.get(self.wallpost_url, params)
        self.assertEqual(response.data['count'], 2)

    def test_create_event_wallpost(self):
        """
        Tests that only the event creator can share a wallpost.
        """
        wallpost_data = {'parent_id': self.event.id,
                         'parent_type': 'event',
                         'text': 'I can share stuff!',
                         'share_with_twitter': True}

        # The owner can share a wallpost
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.owner_token)

        self.assertEqual(
            wallpost.status_code, status.HTTP_201_CREATED,
            'Event owners can share a wallpost.')

    def test_create_wallpost_empty_donation(self):
        """
        Tests that only the event creator can share a wallpost.
        """
        wallpost_data = {'parent_id': self.event.id,
                         'parent_type': 'event',
                         'text': 'I can share stuff!',
                         'donation': None}

        # The owner can post with empty donation
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.owner_token)

        self.assertEqual(
            wallpost.status_code, status.HTTP_201_CREATED,
            'Event owners can post a wallpost with empty donation set.')

    def test_create_event_wallpost_other(self):
        """
        Tests that only the event creator can share a wallpost.
        """
        wallpost_data = {'parent_id': self.event.id,
                         'parent_type': 'event',
                         'text': 'I want to share stuff!',
                         'share_with_twitter': True}

        # Non-owner users can't share a post
        wallpost = self.client.post(self.media_wallpost_url,
                                    wallpost_data,
                                    token=self.other_token)

        self.assertEqual(wallpost.status_code, status.HTTP_403_FORBIDDEN)


class FundingWallpostTest(BluebottleTestCase):
    def setUp(self):
        super(FundingWallpostTest, self).setUp()

        self.owner = BlueBottleUserFactory.create()
        self.owner_token = "JWT {0}".format(self.owner.get_jwt_token())

        self.initiative = InitiativeFactory.create(owner=self.owner)
        self.funding = FundingFactory.create(target=Money(5000, 'EUR'), status='open', initiative=self.initiative)
        self.updates_url = "{}?parent_type=funding&parent_id={}".format(reverse('wallpost_list'), self.funding.id)

    def test_wallposts_with_and_without_donation(self):
        """
        Test that a Wallpost doesn't serializes donation if there isn't one
        """
        TextWallpostFactory.create(content_object=self.funding)
        self.donation = DonationFactory(
            amount=Money(35, 'EUR'),
            user=None,
            activity=self.funding
        )
        self.donation.transitions.succeed()
        self.donation.save()

        response = self.client.get(self.updates_url, token=self.owner_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(
            response.data['results'][0]['donation'],
            {
                'fundraiser': None,
                'amount': {'currency': 'EUR', 'amount': 35.00},
                'user': None,
                'anonymous': False,
                'reward': None,
                'type': 'contributions/donations',
                'id': self.donation.id
            }
        )
        self.assertEqual(response.data['results'][1]['donation'], None)
