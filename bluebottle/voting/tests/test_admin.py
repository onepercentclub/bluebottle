from django.urls import reverse
from fluent_contents.models import Placeholder

from bluebottle.cms.models import HomePage, PollContent
from bluebottle.test.factory_models.cms import HomePageFactory
from bluebottle.test.factory_models.pages import PageFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.voting.tests.factories import PollFactory


class PollAdminTestCase(BluebottleAdminTestCase):

    def setUp(self):
        super().setUp()
        self.init_projects()
        self.client.force_login(self.superuser)
        self.poll = PollFactory.create(title='Favourite colour')

    def test_pages_field_without_blocks(self):
        url = reverse('admin:voting_poll_change', args=(self.poll.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pages')

    def test_pages_field_page_link(self):
        page = PageFactory.create(title='About us')
        placeholder = Placeholder.objects.create_for_object(page, 'blog_contents')
        PollContent.objects.create_for_placeholder(placeholder, poll=self.poll)

        url = reverse('admin:voting_poll_change', args=(self.poll.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('admin:pages_page_change', args=(page.pk,)))
        self.assertContains(response, 'About us')

    def test_pages_field_homepage_link(self):
        HomePage.objects.all().delete()
        homepage = HomePageFactory(pk=1)
        placeholder = Placeholder.objects.create_for_object(homepage, 'content')
        PollContent.objects.create_for_placeholder(placeholder, poll=self.poll)

        url = reverse('admin:voting_poll_change', args=(self.poll.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse('admin:cms_homepage_change', args=(homepage.pk,))
        )
        self.assertContains(response, str(homepage))
