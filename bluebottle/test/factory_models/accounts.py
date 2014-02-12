import factory

from bluebottle.bb_accounts.models import BlueBottleUser


class BlueBottleUserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = BlueBottleUser

    username = factory.Sequence(lambda n: 'user_{0}'.format(n))
    email = factory.Sequence(lambda o: '{0}@onepercentclub.com'.format(o))
    password = factory.PostGenerationMethodCall('set_password', 'testing')
    is_active = True
