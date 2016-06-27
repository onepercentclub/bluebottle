from bluebottle.categories.models import Category
import factory


class CategoryFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Category
        django_get_or_create = ('title',)

    title = factory.Sequence(lambda n: 'Category {0}'.format(n))
    description = factory.Sequence(lambda n: 'Some description {0}'.format(n))
