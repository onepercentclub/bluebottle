# coding=utf-8
from bluebottle.test.factory_models.news import NewsItemFactory
from tenant_schemas.urlresolvers import reverse

from bluebottle.test.utils import BluebottleAdminTestCase


class NewsAdminTest(BluebottleAdminTestCase):
    def setUp(self):
        super(NewsAdminTest, self).setUp()
        self.news = NewsItemFactory()
        self.news_url = reverse('admin:news_newsitem_changelist')
        self.client.force_login(self.superuser)

    def test_form(self):
        response = self.client.get(self.news_url)
        self.assertIn('Add news', response.content)
