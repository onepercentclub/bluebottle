from builtins import object

import factory
from django.core.files.uploadedfile import SimpleUploadedFile

from bluebottle.categories.models import Category, CategoryContent


class CategoryFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Category

    title = factory.Sequence(lambda n: 'Category {0}'.format(n))
    description = factory.Sequence(lambda n: 'Some description {0}'.format(n))


class CategoryContentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = CategoryContent

    category = factory.SubFactory(CategoryFactory)
    title = factory.Sequence(lambda n: 'category_content_title_{}'.format(n))
    description = factory.Sequence(lambda n: 'category_content_description_{}'.format(n))
    image = SimpleUploadedFile(name='test_image.jpg',
                               content=b'',
                               content_type='image/jpeg')
    link_text = factory.Sequence(lambda n: 'read more {}'.format(n))
    link_url = factory.Sequence(lambda n: 'http://{}.test-link-url.com'.format(n))
