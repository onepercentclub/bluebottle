import factory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

BB_USER_MODEL = get_user_model()


class BlueBottleUserFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = BB_USER_MODEL

    username = factory.Sequence(lambda n: u'user_{0}'.format(n))
    email = factory.Sequence(lambda o: u'user_{0}@onepercentclub.com'.format(o))
    password = factory.PostGenerationMethodCall('set_password', 'testing')
    first_name = factory.Sequence(lambda f: u'user_{0}'.format(f))
    last_name = factory.Sequence(lambda l: u'user_{0}'.format(l))
    is_active = True


class GroupFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Group

    name = factory.Sequence(lambda n: u'group_{0}'.format(n))
