import factory

from django.contrib.auth.models import Group

from bluebottle.members.models import Member


class BlueBottleUserFactory(factory.DjangoModelFactory):
    class Meta:
        model = Member

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.Sequence(lambda o: f'user_{o}@onepercentclub.com')
    first_name = factory.Sequence(lambda f: f'user_{f}')
    last_name = factory.Sequence(lambda l: f'user_{l}')
    is_active = True
    is_staff = False
    is_superuser = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        user = super()._create(model_class, *args, **kwargs)
        # ensure the raw password gets set after the initial save
        password = kwargs.pop("password", None)
        if password:
            user.set_password(password)
        user.save()
        return user


class GroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = Group

    name = factory.Sequence(lambda n: f'group_{n}')
