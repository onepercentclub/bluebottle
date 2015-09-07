import factory
from django.utils.timezone import now

from bluebottle.slides.models import Slide
from .accounts import BlueBottleUserFactory


class SlideFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Slide

    author = factory.SubFactory(BlueBottleUserFactory)
    publication_date = now()
    status = Slide.SlideStatus.published
    title = factory.Sequence(lambda n: 'Slide Title {0}'.format(n))
    body = factory.Sequence(lambda n: 'Slide Body {0}'.format(n))
    sequence = factory.Sequence(lambda n: n)


class DraftSlideFactory(SlideFactory):
    status = Slide.SlideStatus.draft
