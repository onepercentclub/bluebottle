from bluebottle.test.utils import BluebottleTestCase
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

# from rest_framework import status
# from rest_framework.test import APITestCase
#
# from bluebottle.test.factory_models.wallposts import TextWallpostFactory
#
# class TextWallpostTestCase(APITestCase)
#     """
#     Base class for test cases for ``text wall post`` module.
#
#     The testing classes for ``text wall post`` module related to the API must
#     subclass this.
#     """
#     def setUp(self):
#     	self.textwallpost = TextWallpostFactory.create()
#
#
# class TextWallpostListTestCase(TextWallpostTestCase)
#     """
#     Test case for ``TextWallpostList`` API view.
#
#     Endpoint: /api/textwallposts/
#     """
#     def test_api_textwallposts_list_endpoint(self):
#         """
#         Ensure we return a text wall post.
#         """
#         response = self.client.get(reverse('textwallposts'))
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(response.data, data)
#
#

#
#
#================================
#
#
import json

from django.core import mail
from django.test import TestCase
from rest_framework import status
from bluebottle.mail import send_mail
from bluebottle.utils.tests import UserTestsMixin
from bluebottle.test.factory_models.tasks import TaskFactory
from bluebottle.test.factory_models.wallposts import TextWallpostFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory, ProjectThemeFactory, ProjectPhaseFactory
from ..models import Reaction



from bluebottle.wallposts import mails


class WallpostReactionApiIntegrationTest(BluebottleTestCase):
    """
    Integration tests for the Project Media Wallpost API.
    """

    def setUp(self):
        super(WallpostReactionApiIntegrationTest, self).setUp()

        self.init_projects()

        self.some_wallpost = TextWallpostFactory.create()
        self.another_wallpost = TextWallpostFactory.create()
        
        self.some_user = BlueBottleUserFactory.create(password='testing', first_name='someName', last_name='someLast')
        self.some_token = "JWT {0}".format(self.some_user.get_jwt_token())

        self.another_user = BlueBottleUserFactory.create(password='testing2', first_name='anotherName', last_name='anotherLast')
        self.another_token = "JWT {0}".format(self.another_user.get_jwt_token())

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
                                            {'text': reaction_text, 'wallpost': self.some_wallpost.id},
                                            token=self.some_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(reaction_text in response.data['text'])

        # Retrieve the created Reaction
        reaction_detail_url = reverse('wallpost_reaction_detail', kwargs={'pk': response.data['id']})
        response = self.client.get(reaction_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(reaction_text in response.data['text'])

        # Update the created Reaction by author.
        new_reaction_text = 'HEAR!!! HEAR!!!'
        response = self.client.put(reaction_detail_url,
                                    {'text': new_reaction_text, 'wallpost': self.some_wallpost.id},
                                    token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(new_reaction_text in response.data['text'])

        # switch to another user
        self.client.logout()

        # Retrieve the created Reaction by non-author should work
        response = self.client.get(reaction_detail_url, token=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(new_reaction_text in response.data['text'])

        # Delete Reaction by non-author should not work
        self.client.logout()
        response = self.client.delete(reaction_detail_url, token=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response)

        # Create a Reaction by another user
        another_reaction_text = "I'm not so sure..."
        response = self.client.post(self.wallpost_reaction_url,
                                    {'text': another_reaction_text, 'wallpost': self.some_wallpost.id},
                                    token=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        # Only check the substring because the single quote in "I'm" is escaped.
        # https://docs.djangoproject.com/en/dev/topics/templates/#automatic-html-escaping
        self.assertTrue('not so sure' in response.data['text'])

        # retrieve the list of Reactions for this Wallpost should return two
        response = self.client.get(self.wallpost_reaction_url, {'wallpost': self.some_wallpost.id},
                                   token=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 2)
        self.assertTrue(new_reaction_text in response.data['results'][0]['text'])

        # Only check the substring because the single quote in "I'm" is escaped.
        # https://docs.djangoproject.com/en/dev/topics/templates/#automatic-html-escaping
        self.assertTrue('not so sure' in response.data['results'][1]['text'])

        # Delete Reaction by author should work
        response = self.client.delete(reaction_detail_url, token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response)

        # Retrieve the deleted Reaction should fail
        response = self.client.get(reaction_detail_url, token=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)


    def test_reactions_on_multiple_objects(self):
        """
        Tests for multiple reactions and unauthorized reaction updates.
        """

        # Create two reactions.
        reaction_text_1 = 'Great job!'
        response = self.client.post(self.wallpost_reaction_url,
                                    {'text': reaction_text_1, 'wallpost': self.some_wallpost.id},
                                    token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(reaction_text_1 in response.data['text'])

        reaction_text_2 = 'This is a really nice post.'
        response = self.client.post(self.wallpost_reaction_url,
                                    {'text': reaction_text_2, 'wallpost': self.some_wallpost.id},
                                    token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(reaction_text_2 in response.data['text'])


        # Check the size of the reaction list is correct.
        response = self.client.get(self.wallpost_reaction_url, {'wallpost': self.some_wallpost.id},
                                    token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 2)

        # Check that the reaction listing without a wallpost id is working.
        response = self.client.get(self.wallpost_reaction_url, token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 2)

        # Create a reaction on second blog post.
        reaction_text_3 = 'Super!'
        response = self.client.post(self.wallpost_reaction_url,
                                    {'text': reaction_text_3, 'wallpost': self.another_wallpost.id},
                                    token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(reaction_text_3 in response.data['text'])
        # Save the detail url to be used in the authorization test below.
        second_reaction_detail_url = reverse('wallpost_reaction_detail', kwargs={'pk': response.data['id']})

        # Check that the size and data in the first reaction list is correct.
        response = self.client.get(self.wallpost_reaction_url, {'wallpost': self.some_wallpost.id},
                                    token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        # filter_fields seems to do not work...WHYYYYY
        self.assertEqual(response.data['count'], 2)

        self.assertTrue(reaction_text_1 in response.data['results'][0]['text'])
        self.assertTrue(reaction_text_2 in response.data['results'][1]['text'])

        # Check that the size and data in the second reaction list is correct.
        response = self.client.get(self.wallpost_reaction_url, 
                                    {'wallpost': self.another_wallpost.id},
                                    token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertTrue(reaction_text_3 in response.data['results'][0]['text'])

        # Test that a reaction update from a user who is not the author is forbidden.
        response = self.client.post(second_reaction_detail_url, 
                                    {'text': 'Can I update this reaction?'},
                                    token=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED, response.data)


    # def test_embedded_reactions(self):
        """
            Test reactions embedded in Project Wallpost Api calls
        """
        #
        # # Create two Reactions and retrieve the related Project Text Wallpost should have the embedded
        # self.client.login(email=self.some_user.email, password='testing')
        # reaction1_text = "Hear! Hear!"
        # response = self.client.post(self.wallpost_reaction_url,
        #                             {'text': reaction1_text, 'wallpost': self.some_wallpost.id})
        #
        # reaction1_detail_url = reverse(self.wallpost_reaction_url, kwargs={'pk':response.data['id']})
        # reaction2_text = "This is cool!"
        # self.client.post(self.wallpost_reaction_url, {'text': reaction2_text, 'wallpost': self.some_wallpost.id})
        # some_wallpost_detail_url = "{0}{1}".format(self.wallpost_url, str(self.some_wallpost.id))
        # response = self.client.get(some_wallpost_detail_url)
        # self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        # self.assertEqual(len(response.data['reactions']), 2)
        # self.assertTrue(reaction1_text in response.data['reactions'][0]['text'])
        # self.assertTrue(reaction2_text in response.data['reactions'][1]['text'])
#
#         # Create a Reaction to another Wallpost and retrieve that Wallpost should return one embedded reaction
#         reaction3_text = "That other post was way better..."
#         self.client.post(self.wallpost_reaction_url, {'text': reaction3_text, 'wallpost': self.another_wallpost.id})
#         another_wallpost_detail_url = "{0}{1}".format(self.wallpost_url, str(self.another_wallpost.id))
#         response = self.client.get(another_wallpost_detail_url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(len(response.data['reactions']), 1)
#         self.assertTrue(reaction3_text in response.data['reactions'][0]['text'])
#
#         # The first Wallpost should still have just two reactions
#         response = self.client.get(some_wallpost_detail_url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(len(response.data['reactions']), 2)
#
#         # Delete the first reaction
#         response = self.client.delete(reaction1_detail_url)
#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.data)
#
#         # The first Wallpost should have only one reaction now
#         response = self.client.get(some_wallpost_detail_url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(len(response.data['reactions']), 1)
#
#
# class WallpostApiRegressionTests(UserTestsMixin, TestCase): #ProjectWallpostTestsMixin,
#     """
#     Integration tests for the Project Media Wallpost API.
#     """
#
#     def setUp(self):
#         self.user = self.create_user()
#         self.wallpost = self.create_project_text_wallpost(author=self.user)
#
#         self.media_wallposts_url = '/api/wallposts/mediawallposts/'
#         self.text_wallposts_url = '/api/wallposts/textwallposts/'
#         self.wallposts_url = '/api/wallposts/'
#         self.wallpost_reaction_url = '/api/wallposts/reactions/'
#
#     def test_html_javascript_propperly_escaped(self):
#         """
#         https://onepercentclub.atlassian.net/browse/BB-130
#         """
#
#         # Create a Reaction and check that the HTML is escaped.
#         self.client.login(email=self.user.email, password='password')
#         reaction_text = "<marquee>WOOOOOO</marquee>"
#         # The paragraph tags are added by the linebreak filter.
#         escaped_reaction_text = "<p>WOOOOOO</p>"
#         response = self.client.post(self.wallpost_reaction_url, {'text': reaction_text, 'wallpost': self.wallpost.id})
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
#         self.assertEqual(escaped_reaction_text, response.data['text'])
#
#     def test_link_properly_created(self):
#         """
#         https://onepercentclub.atlassian.net/browse/BB-136
#         """
#
#         # Create a Reaction and check that the HTML link is properly created.
#         self.client.login(email=self.user.email, password='password')
#         reaction_text = "www.1procentclub.nl"
#         # The paragraph tags and the anchor are added by the filters we're using.
#         escaped_reaction_text = '<p><a target="_blank" href="http://www.1procentclub.nl" rel="nofollow">www.1procentclub.nl</a></p>'
#         response = self.client.post(self.wallpost_reaction_url, {'text': reaction_text, 'wallpost': self.wallpost.id})
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
#         self.assertEqual(escaped_reaction_text, response.data['text'])


class WallpostMailTests(UserTestsMixin, BluebottleTestCase): #ProjectWallpostTestsMixin,
    
    def setUp(self):
        from bluebottle.bb_projects.models import ProjectPhase, ProjectTheme
        
        super(WallpostMailTests, self).setUp()

        self.init_projects()

        self.user_a = self.create_user(email='a@example.com', first_name='aname ', last_name='alast')
        self.user_b = self.create_user(email='b@example.com', first_name='bname ', last_name='blast')
        self.user_c = self.create_user(email='c@example.com', first_name='cname ', last_name='clast')

        #self.project = self.create_project(owner=self.user_a)

        self.theme_1 = ProjectTheme.objects.get(name='Education')
        self.phase_1 = ProjectPhase.objects.get(slug='campaign')

        self.project_1 = ProjectFactory.create(
            owner=self.user_a, status=self.phase_1, theme=self.theme_1)

        self.task_1 = TaskFactory(author=self.user_a, project=self.project_1)

    def test_translated_mail_subject(self):
        self.user_a.primary_language = 'en'
        self.user_a.save()

        send_mail(
            template_name='project_wallpost_reaction_new.mail',
            subject=_('Username'),
            obj=self.project_1,
            to=self.user_a,
            author=self.user_b
        )

        self.assertEqual(len(mail.outbox), 1)
        mail_message = mail.outbox[0]

        self.assertEquals(mail_message.subject, 'Username')

        self.user_a.primary_language = 'nl'
        self.user_a.save()

        send_mail(
            template_name='project_wallpost_reaction_new.mail',
            subject=_('Username'),
            obj=self.project_1,
            to=self.user_a,
            author=self.user_b
        )

        self.assertEqual(len(mail.outbox), 2)
        mail_message = mail.outbox[1]

        self.assertEquals(mail_message.subject, 'Gebruikersnaam')

    def test_new_wallpost_by_a_on_project_by_a(self):
        """
        Project by A + Wallpost by A => No mails.
        """
        # Object by A
        # |
        # +-- Wallpost by A (+)

        post = TextWallpostFactory.create(content_object=self.project_1, author=self.user_a)

        # Mailbox should not contain anything.
        self.assertEqual(len(mail.outbox), 0)

    def test_new_wallpost_by_b_on_project_by_a(self):
        """
        Project by A + Wallpost by B => Mail to (project owner) A
        """
        # Object by A
        # |
        # +-- Wallpost by B (+)

        post = TextWallpostFactory.create(content_object=self.project_1, author=self.user_b)

        # Mailbox should contain an email to project owner.
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]

        self.assertEqual(m.to, [self.user_a.email])

    def test_new_reaction_by_a_on_wallpost_a_on_project_by_a(self):
        """
        Project by A + Wallpost by A + Reaction by A => No mails.
        """
        # Object by A
        # |
        # +-- Wallpost by A
        # |   |
        # |   +-- Reaction by A (+)

        w = TextWallpostFactory.create(content_object=self.project_1, author=self.user_a)

        # Empty outbox.
        mail.outbox = []
        Reaction.objects.create(text='Hello world', wallpost=w, author=self.user_a)

        # Mailbox should not contain anything.
        self.assertEqual(len(mail.outbox), 0)

    def test_new_reaction_by_b_on_wallpost_a_on_project_by_a(self):
        """
        Project by A + Wallpost by A + Reaction by B => Mail to (reaction author) A.
        """
        # Object by A
        # |
        # +-- Wallpost by A
        # |   |
        # |   +-- Reaction by A
        # |   |
        # |   +-- Reaction by B (+)

        w = TextWallpostFactory.create(content_object=self.project_1, author=self.user_a)

        Reaction.objects.create(text='Hello world', wallpost=w, author=self.user_a)

        # Empty outbox.
        mail.outbox = []
        Reaction.objects.create(text='Hello world', wallpost=w, author=self.user_b)

        # Mailbox should contain an email to author of reaction a.
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]

        self.assertEqual(m.to, [self.user_a.email])

    def test_new_reaction_by_a_on_wallpost_b_on_project_by_a(self):
        """
        Project by A + Wallpost by B + Reaction by A => Mail to (reaction author) B.
        """
        # Object by A
        # |
        # +-- Wallpost by B
        #     |
        #     +-- Reaction by A (+)

        w = TextWallpostFactory.create(content_object=self.project_1, author=self.user_b)

        # Empty outbox.
        mail.outbox = []
        Reaction.objects.create(text='Hello world', wallpost=w, author=self.user_a)

        # Mailbox should contain an email to author of reaction b.
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]

        self.assertEqual(m.to, [self.user_b.email])

    def test_new_reaction_by_b_on_wallpost_b_on_project_by_a(self):
        """
        Project by A + Wallpost by B + Reaction by B => Mail to (project owner) A.
        """
        # Object by A
        # |
        # +-- Wallpost by B
        #     |
        #     +-- Reaction by A
        #     |
        #     +-- Reaction by B (+)

        w = TextWallpostFactory.create(content_object=self.project_1, author=self.user_b)
        Reaction.objects.create(text='Hello world', wallpost=w, author=self.user_a)

        # Empty outbox.
        mail.outbox = []
        Reaction.objects.create(text='Hello world', wallpost=w, author=self.user_b)

        # Mailbox should contain an email to project owner.
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]

        self.assertEqual(m.to, [self.user_a.email])

    def test_new_reaction_by_c_on_wallpost_b_on_project_by_a(self):
        """
        Project by A + Wallpost by B + Reaction by C => Mail to (project owner) A + Mail to (reaction author) B
        """
        # Object by A
        # |
        # +-- Wallpost by B
        #     |
        #     +-- Reaction by A
        #     |
        #     +-- Reaction by B
        #     |
        #     +-- Reaction by C (+)

        w = TextWallpostFactory.create(content_object=self.project_1, author=self.user_b)
        Reaction.objects.create(text='Hello world', wallpost=w, author=self.user_a)
        Reaction.objects.create(text='Hello world', wallpost=w, author=self.user_b)

        # Empty outbox.
        mail.outbox = []
        Reaction.objects.create(text='Hello world', wallpost=w, author=self.user_c)

        # Mailbox should contain an email to project owner.
        self.assertEqual(len(mail.outbox), 2)
        m1 = mail.outbox[0]
        m2 = mail.outbox[1]

        self.assertListEqual([m2.to[0], m1.to[0]], [self.user_a.email, self.user_b.email])

    def test_new_wallpost_by_b_on_task_by_a(self):
        """
        Task by A + Wallpost by B => Mail to (task owner) A
        """
        # Object by A
        # |
        # +-- Wallpost by B (+)

        post = TextWallpostFactory.create(content_object=self.task_1, author=self.user_b)

        # Mailbox should contain an email to project owner.
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]

        self.assertEqual(m.to, [self.user_a.email])
