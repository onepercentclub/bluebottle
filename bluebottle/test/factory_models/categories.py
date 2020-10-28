from django.core.files.uploadedfile import SimpleUploadedFile
from bluebottle.categories.models import Category, CategoryContent
import factory


class CategoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = Category

    title = factory.Sequence(lambda n: f'Category {n}')
    description = factory.Sequence(lambda n: f'Some description {n}')


class CategoryContentFactory(factory.DjangoModelFactory):
    class Meta:
        model = CategoryContent

    category = factory.SubFactory(CategoryFactory)
    title = factory.Sequence(lambda n: f'category_content_title_{n}')
    description = factory.Sequence(lambda n: f'category_content_description_{n}')
    image = SimpleUploadedFile(name='test_image.jpg',
                               content=b'',
                               content_type='image/jpeg')
    video_url = factory.Sequence(lambda n: f'http://{n}.test-video-url.com')
    link_text = factory.Sequence(lambda n: f'read more {n}')
    link_url = factory.Sequence(lambda n: f'http://{n}.test-link-url.com')
