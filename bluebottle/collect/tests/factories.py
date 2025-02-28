from builtins import object

import factory.fuzzy
from pytz import UTC

from bluebottle.test.factory_models import generate_rich_text

from bluebottle.fsm.factory import FSMModelFactory
from bluebottle.test.factory_models.geo import GeolocationFactory

from bluebottle.collect.models import CollectActivity, CollectContributor, CollectType
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.utils.models import Language


class CollectTypeFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = CollectType

    disabled = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = super(CollectTypeFactory, cls)._create(model_class, *args, **kwargs)
        for language in Language.objects.all():
            obj.set_current_language(language.code)
            obj.name = "Name {} {}".format(language.code, obj.id)
        obj.save()
        return obj

    unit = factory.Faker('word')
    unit_plural = factory.Faker('word')


class CollectActivityFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = CollectActivity

    title = factory.Faker('sentence')
    slug = factory.Faker('slug')
    description = factory.LazyFunction(generate_rich_text)

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    collect_type = factory.SubFactory(CollectTypeFactory)
    location = factory.SubFactory(GeolocationFactory)
    start = factory.Faker('future_date', end_date="+20d", tzinfo=UTC)
    end = factory.Faker('future_date', end_date="+2d", tzinfo=UTC)


class CollectContributorFactory(FSMModelFactory):
    class Meta(object):
        model = CollectContributor

    activity = factory.SubFactory(CollectActivityFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
