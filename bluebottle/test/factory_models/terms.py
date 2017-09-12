from bluebottle.terms.models import Terms, TermsAgreement
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
import factory
import factory.fuzzy
from django.utils.timezone import now
from datetime import timedelta


class TermsFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Terms
        django_get_or_create = ('version',)

    author = factory.SubFactory(BlueBottleUserFactory)
    date = now() - timedelta(weeks=4)
    contents = u"Apply yourself!"
    version = "1.0"


class TermsAgreementFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = TermsAgreement

    user = factory.SubFactory(BlueBottleUserFactory)
    terms = factory.SubFactory(TermsFactory)
