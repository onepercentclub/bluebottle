from django.core.files.uploadedfile import SimpleUploadedFile
from bluebottle.categories.models import Category, CategoryContent
import factory


class CategoryFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Category
        django_get_or_create = ('title',)

    title = factory.Sequence(lambda n: 'Category {0}'.format(n))
    description = factory.Sequence(lambda n: 'Some description {0}'.format(n))


class CategoryContentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = CategoryContent
        django_get_or_create = ('title',)

    category = factory.SubFactory(CategoryFactory)
    title = factory.Sequence(lambda n: 'category_content_title_{}'.format(n))
    description = factory.Sequence(lambda n: 'category_content_description_{}'.format(n))
    image = SimpleUploadedFile(name='test_image.jpg',
                               content=b'',
                               content_type='image/jpeg')
    video_url = factory.Sequence(lambda n: 'http://{}.test-video-url.com'.format(n))
    link = factory.Sequence(lambda n: 'http://{}.test-link-url.com'.format(n))
