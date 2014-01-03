import factory
import logging

from bluebottle.accounts.models import BlueBottleUser

# Suppress debug information for Factory Boy
logging.getLogger('factory').setLevel(logging.WARN)


class BlueBottleUserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = BlueBottleUser

    email = 'john.doe@onepercentclub.com'
    username = 'johndoe'
    password = factory.PostGenerationMethodCall('set_password', 'testing')
