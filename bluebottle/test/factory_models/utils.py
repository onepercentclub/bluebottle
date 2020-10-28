import factory
from factory.fuzzy import FuzzyText

from bluebottle.utils.models import Language


class LanguageFactory(factory.DjangoModelFactory):

    class Meta:
        model = Language
        django_get_or_create = ('language_name',)

    language_name = factory.Sequence(lambda n: f'Language_{n}')
    code = FuzzyText(length=2)
    native_name = factory.Sequence(lambda n: f'Lingvo_{n}')
