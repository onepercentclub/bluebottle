import factory

from django.contrib.auth import get_user_model


BB_USER_MODEL = get_user_model()


class BlueBottleUserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = BB_USER_MODEL

    email = factory.Sequence(lambda n: 'john.doe{0}@onepercentclub.com'.format(n))
    username = factory.Sequence(lambda n: 'Johndoe{0}'.format(n))
    password = factory.PostGenerationMethodCall('set_password', 'testing')
    is_active = True
