from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.categories import CategoryFactory


class TestCategoryModel(BluebottleTestCase):
    """
        save() automatically updates some fields, specifically
        the status field. Make sure it picks the right one
    """
    def test_save_slug(self):
        category = CategoryFactory.create(title='test-title')

        self.assertEqual(category.slug, 'test-title')

    def test_absolute_url(self):
        category = CategoryFactory.create(title='test-title')

        self.assertEqual(
            category.get_absolute_url(),
            'https://testserver/projects/?category=test-title'
        )
