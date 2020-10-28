import factory

from bluebottle.segments.models import Segment, SegmentType


class SegmentTypeFactory(factory.DjangoModelFactory):

    class Meta:
        model = SegmentType

    name = factory.Faker('word')
    is_active = True


class SegmentFactory(factory.DjangoModelFactory):

    class Meta:
        model = Segment

    name = factory.Faker('word')

    alternate_names = factory.List([
        factory.Faker('word')
    ])

    type = factory.SubFactory(SegmentTypeFactory)
