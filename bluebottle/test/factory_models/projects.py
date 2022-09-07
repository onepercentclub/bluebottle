from builtins import object
import factory

from bluebottle.initiatives.models import Theme
from bluebottle.utils.models import Language


class ThemeFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Theme
        django_get_or_create = ('slug',)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = super(ThemeFactory, cls)._create(model_class, *args, **kwargs)
        for language in Language.objects.all():
            obj.set_current_language(language.code)
            obj.name = "Name {} {}".format(language.code, obj.id)
        obj.save()
        return obj

    name = factory.Sequence(lambda n: 'Theme_{0}'.format(n))
    slug = name
    description = 'Theme factory model'
