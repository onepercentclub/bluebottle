from bluebottle.terms.models import Terms
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
import factory
import factory.fuzzy
from django.utils.timezone import now
from datetime import timedelta


class TermsFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Terms
    FACTORY_DJANGO_GET_OR_CREATE = ('version',)

    author = factory.SubFactory(BlueBottleUserFactory)
    date = now() - timedelta(weeks=4)
    contents = u"Apply yourself!"
    version = "1.0"
