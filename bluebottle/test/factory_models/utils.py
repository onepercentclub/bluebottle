import factory

from bluebottle.utils.models import Language


class LanguageFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = Language
        django_get_or_create = ('language_name',)

    language_name = factory.Sequence(lambda n: 'Language_{0}'.format(n))
    code = factory.Sequence(lambda n: 'L{0}'.format(n))
    native_name = factory.Sequence(lambda n: 'Lingvo_{0}'.format(n))
