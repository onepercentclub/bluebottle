from builtins import object
import factory
from factory.fuzzy import FuzzyChoice

from django.conf import settings

from bluebottle.utils.models import Language


class LanguageFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = Language
        django_get_or_create = ('language_name',)

    language_name = factory.Sequence(lambda n: 'Language_{0}'.format(n))
    code = FuzzyChoice([code for code, name in settings.LANGUAGES if len(code) == 2])
    native_name = factory.Sequence(lambda n: 'Lingvo_{0}'.format(n))
