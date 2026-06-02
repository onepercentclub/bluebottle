from builtins import object
import factory

from bluebottle.initiatives.models import Theme


class ThemeFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Theme

    name = factory.Sequence(lambda n: 'Theme_{0}'.format(n))
    slug = factory.Sequence(lambda n: 'theme-{0}'.format(n))
    description = 'Theme factory model'
