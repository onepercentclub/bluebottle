import factory
from bluebottle.redirects.models import Redirect


class RedirectFactory(factory.DjangoModelFactory):
    class Meta:
        model = Redirect

    old_path = factory.Sequence(lambda n: f'/old-{n}')
    new_path = factory.Sequence(lambda n: f'/new/{n}')
