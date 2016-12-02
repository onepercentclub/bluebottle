from django.core.urlresolvers import reverse

from rest_framework import status
from fluent_contents.tests.factories import create_placeholder, create_content_item

from bluebottle.cms.models import StatsContent
from bluebottle.test.factory_models.cms import ResultPageFactory, StatFactory, StatsFactory
from bluebottle.test.utils import BluebottleTestCase


class ResultPageTestCase(BluebottleTestCase):
    """
    Integration tests for the Results Page API.
    """

    def setUp(self):
        super(ResultPageTestCase, self).setUp()

        self.page = ResultPageFactory()
        ph = create_placeholder(page=self.page)
        stats = StatsFactory()
        self.stat = StatFactory(stats=stats)
        create_content_item(StatsContent, placeholder=ph, stats=stats)
        ph.save()

    def test_results(self):
        url = reverse('result-page-detail', kwargs={'pk': self.page.id})

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, 1)
