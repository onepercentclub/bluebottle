import factory
import logging

from django.contrib.auth import get_user_model

# Suppress debug information for Factory Boy
logging.getLogger('factory').setLevel(logging.WARN)


BB_USER_MODEL = get_user_model()


class BlueBottleUserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = BB_USER_MODEL

    email = 'john.doe@onepercentclub.com'
    username = 'johndoe'
    password = factory.PostGenerationMethodCall('set_password', 'testing')
    is_active = True
