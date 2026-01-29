import factory

from bluebottle.segments.models import Segment, SegmentType
from bluebottle.test.factory_models import generate_rich_text
from bluebottle.utils.models import Language


class SegmentTypeFactory(factory.DjangoModelFactory):
    class Meta():
        model = SegmentType

    name = factory.Faker('sentence')
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = super(SegmentTypeFactory, cls)._create(model_class, *args, **kwargs)

        base_name = obj.name

        for language in Language.objects.all():
            obj.set_current_language(language.full_code)
            obj.name = base_name

        obj.save()
        return obj


class SegmentFactory(factory.DjangoModelFactory):

    class Meta():
        model = Segment

    name = factory.Sequence(lambda n: 'Segment - {0}'.format(n))

    alternate_names = factory.List([
        factory.Faker('word')
    ])

    segment_type = factory.SubFactory(SegmentTypeFactory)

    email_domains = ['example.com']

    slogan = factory.Faker('sentence')
    story = factory.LazyFunction(generate_rich_text)
    background_color = factory.Faker('color')

    logo = factory.django.ImageField(color='blue')
    cover_image = factory.django.ImageField(color='red')

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = super(SegmentFactory, cls)._create(model_class, *args, **kwargs)

        base_name = obj.name

        for language in Language.objects.all():
            obj.set_current_language(language.full_code)
            obj.name = base_name

        obj.save()
        return obj
