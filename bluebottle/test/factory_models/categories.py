from bluebottle.categories.models import Category
import factory


class CategoryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Category
    FACTORY_DJANGO_GET_OR_CREATE = ('title',)

    title = factory.Sequence(lambda n: 'Category {0}'.format(n))
    description = factory.Sequence(lambda n: 'Some description {0}'.format(n))
