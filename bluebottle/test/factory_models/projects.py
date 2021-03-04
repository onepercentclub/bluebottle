from builtins import object
import factory

from bluebottle.initiatives.models import Theme


class ThemeFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Theme
        django_get_or_create = ('slug',)

    name = factory.Sequence(lambda n: 'Theme_{0}'.format(n))
    slug = name
    description = 'Theme factory model'
