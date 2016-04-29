import factory
from bluebottle.redirects.models import Redirect


class RedirectFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Redirect

    old_path = factory.Sequence(lambda n: '/old-{0}'.format(n))
    new_path = factory.Sequence(lambda n: '/new/{0}'.format(n))
    fallback_redirect = 'default'
