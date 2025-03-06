import factory

from bluebottle.test.factory_models import generate_rich_text
from bluebottle.segments.models import Segment, SegmentType


class SegmentTypeFactory(factory.DjangoModelFactory):
    class Meta():
        model = SegmentType

    name = factory.Faker('sentence')
    is_active = True


class SegmentFactory(factory.DjangoModelFactory):

    class Meta():
        model = Segment

    name = factory.Sequence(lambda n: 'Segment - {0}'.format(n))

    alternate_names = factory.List([
        factory.Faker('word')
    ])

    segment_type = factory.SubFactory(SegmentTypeFactory)

    email_domains = ['example.com']

    tag_line = factory.Faker('sentence')
    story = factory.LazyFunction(generate_rich_text)
    background_color = factory.Faker('color')

    logo = factory.django.ImageField(color='blue')
    cover_image = factory.django.ImageField(color='red')
