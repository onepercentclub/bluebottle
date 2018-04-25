# coding=utf-8
from bluebottle.test.factory_models.slides import SlideFactory
from tenant_schemas.urlresolvers import reverse

from bluebottle.test.utils import BluebottleAdminTestCase


class SlideAdminTest(BluebottleAdminTestCase):
    def setUp(self):
        super(SlideAdminTest, self).setUp()
        self.news = SlideFactory()
        self.news_url = reverse('admin:slides_slide_changelist')
        self.client.force_login(self.superuser)

    def test_form(self):
        response = self.client.get(self.news_url)
        self.assertIn('Add slide', response.content)
