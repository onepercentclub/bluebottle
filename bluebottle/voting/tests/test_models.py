from django.utils.translation import override
from fluent_contents.models import Placeholder

from bluebottle.cms.models import PollContent
from bluebottle.test.factory_models.pages import PageFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.voting.models import Poll, PollOption


class PollModelTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.init_projects()
        self.poll = Poll()
        self.poll.set_current_language('en')
        self.poll.title = 'Favourite colour'
        self.poll.save()

        self.option = PollOption(poll=self.poll)
        self.option.set_current_language('en')
        self.option.title = 'Blue'
        self.option.save()

        page = PageFactory.create()
        placeholder = Placeholder.objects.create_for_object(page, 'blog_contents')
        self.block = PollContent.objects.create_for_placeholder(
            placeholder, poll=self.poll
        )

    def test_str_without_active_language(self):
        with override(None):
            self.assertEqual(str(Poll.objects.get(pk=self.poll.pk)), 'Favourite colour')
            self.assertEqual(
                str(PollOption.objects.get(pk=self.option.pk)), 'Blue'
            )
            self.assertEqual(
                str(PollContent.objects.get(pk=self.block.pk)), 'Favourite colour'
            )
