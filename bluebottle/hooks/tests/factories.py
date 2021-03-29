import factory.fuzzy

from bluebottle.hooks.models import WebHook


class WebHookFactory(factory.DjangoModelFactory):

    class Meta():
        model = WebHook

    url = factory.Faker('url')
