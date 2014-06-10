import factory

from django.contrib.auth import get_user_model

BB_USER_MODEL = get_user_model()


class BlueBottleUserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = BB_USER_MODEL

    username = factory.Sequence(lambda n: u'user_{0}'.format(n))
    email = factory.Sequence(lambda o: u'user_{0}@onepercentclub.com'.format(o))
    password = factory.PostGenerationMethodCall('set_password', 'testing')
    first_name = factory.Sequence(lambda f: u'user_{0}'.format(f))
    last_name = factory.Sequence(lambda l: u'user_{0}'.format(l))
    full_name = factory.LazyAttribute(lambda a: '{0} {1}'.format(a.first_name, a.last_name).lower())
    is_active = True
