import os
from builtins import object

import factory
from django.core.files import File

from bluebottle.organizations.models import OrganizationContact, Organization
from .accounts import BlueBottleUserFactory


class OrganizationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Organization

    name = factory.Sequence(lambda n: 'Organization_{0}'.format(n))
    slug = factory.Sequence(lambda n: 'organization_{0}'.format(n))
    website = 'https://goodup.com'
    owner = factory.SubFactory(BlueBottleUserFactory)

    @staticmethod
    def _save_file(obj, field_name, path, create):
        with open(path, 'rb') as file:
            getattr(obj, field_name).save(
                os.path.basename(path), File(file), save=create
            )

    @factory.post_generation
    def image(obj, create, extracted, **kwargs):
        """Pass `image=<path>` to store that file as the organization image."""
        if extracted:
            OrganizationFactory._save_file(obj, 'image', extracted, create)

    @factory.post_generation
    def logo(obj, create, extracted, **kwargs):
        """Pass `logo=<path>` to store that file as the organization logo."""
        if extracted:
            OrganizationFactory._save_file(obj, 'logo', extracted, create)

    @factory.post_generation
    def created(obj, create, extracted, **kwargs):
        """
        Pass `created=<datetime>` to override the creation date. `created` uses
        auto_now_add, so it is set after the instance is created and saved again.
        """
        if extracted:
            obj.created = extracted
            if create:
                obj.save(update_fields=['created'])


class OrganizationContactFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = OrganizationContact

    name = factory.Sequence(lambda n: 'Contact_{0}'.format(n))
    phone = factory.Sequence(lambda n: '555-{0}'.format(n))
    email = factory.Sequence(lambda n: '{0}@example.com'.format(n))
    owner = factory.SubFactory(BlueBottleUserFactory)
