import factory

from bluebottle.initiatives.models import Initiative, Theme

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class ThemeFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Theme

    name = factory.Sequence(lambda n: 'Theme {0}'.format(n))


class InitiativeFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Initiative

    review_status = Initiative.ReviewStatus.created
    title = factory.Sequence(lambda n: 'Initiative {0}'.format(n))
    owner = factory.SubFactory(BlueBottleUserFactory)
    reviewer = factory.SubFactory(BlueBottleUserFactory)
    theme = factory.SubFactory(ThemeFactory)
