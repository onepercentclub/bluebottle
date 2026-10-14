from builtins import object
import factory

from bluebottle.organizations.models import OrganizationContact, Organization
from bluebottle.utils.models import Language
from .accounts import BlueBottleUserFactory


class OrganizationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Organization

    name = factory.Sequence(lambda n: 'Organization_{0}'.format(n))
    slug = factory.Sequence(lambda n: 'organization_{0}'.format(n))
    website = 'https://goodup.com'
    owner = factory.SubFactory(BlueBottleUserFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        slogan = kwargs.pop('slogan', 'Some info')
        story = kwargs.pop('story', None)
        obj = super(OrganizationFactory, cls)._create(model_class, *args, **kwargs)
        languages = list(Language.objects.all())
        language_codes = (
            [language.full_code for language in languages]
            if languages else ['en', 'nl']
        )
        for code in language_codes:
            obj.set_current_language(code)
            obj.slogan = slogan
            if story is not None:
                obj.story = story
        obj.save()
        return obj


class OrganizationContactFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = OrganizationContact

    name = factory.Sequence(lambda n: 'Contact_{0}'.format(n))
    phone = factory.Sequence(lambda n: '555-{0}'.format(n))
    email = factory.Sequence(lambda n: '{0}@example.com'.format(n))
    owner = factory.SubFactory(BlueBottleUserFactory)
