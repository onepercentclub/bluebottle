import factory

from bluebottle.bb_accounts.tests.baseuser.models import TestBaseUser


class BlueBottleUserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = TestBaseUser

    username = factory.Sequence(lambda n: u'user_{0}'.format(n))
    email = factory.Sequence(lambda o: u'user_{0}@onepercentclub.com'.format(o))
    password = factory.PostGenerationMethodCall('set_password', 'testing')
    is_active = True
