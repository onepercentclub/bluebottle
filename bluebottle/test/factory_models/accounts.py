from builtins import object

import factory
from django.contrib.auth.models import Group

from bluebottle.members.models import Member


class BlueBottleUserFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Member

    username = factory.Sequence(lambda n: u'user_{0}'.format(n))
    email = factory.Sequence(lambda o: u'user_{0}@onepercentclub.com'.format(o))
    first_name = factory.Sequence(lambda name: u'user_{0}'.format(name))
    last_name = factory.Sequence(lambda name: u'user_{0}'.format(name))
    is_active = True
    is_staff = False
    is_superuser = False
    region_manager = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        user = super(BlueBottleUserFactory, cls)._create(model_class, *args, **kwargs)
        # ensure the raw password gets set after the initial save
        password = kwargs.pop("password", None)
        if password:
            user.set_password(password)
        user.save()
        return user


class GroupFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Group

    name = factory.Sequence(lambda n: u'group_{0}'.format(n))
