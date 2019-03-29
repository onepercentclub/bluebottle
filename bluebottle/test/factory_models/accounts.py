import factory

from django.contrib.auth.models import Group

from bluebottle.members.models import Member


class BlueBottleUserFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Member

    username = factory.Sequence(lambda n: u'user_{0}'.format(n))
    email = factory.Sequence(lambda o: u'user_{0}@onepercentclub.com'.format(o))
    first_name = factory.Sequence(lambda f: u'user_{0}'.format(f))
    last_name = factory.Sequence(lambda l: u'user_{0}'.format(l))
    is_active = True
    is_staff = False
    is_superuser = False

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(BlueBottleUserFactory, cls)._prepare(False, **kwargs)

        if password:
            user.set_password(password)

        if create:
            user.save()

        return user


class GroupFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Group

    name = factory.Sequence(lambda n: u'group_{0}'.format(n))
