import factory
from django.utils.timezone import now

from bluebottle.slides.models import Slide
from .accounts import BlueBottleUserFactory


class SlideFactory(factory.DjangoModelFactory):
    class Meta:
        model = Slide

    author = factory.SubFactory(BlueBottleUserFactory)
    publication_date = now()
    status = Slide.SlideStatus.published
    title = factory.Sequence(lambda n: f'Slide Title {n}')
    body = factory.Sequence(lambda n: f'Slide Body {n}')
    sequence = factory.Sequence(lambda n: n)


class DraftSlideFactory(SlideFactory):
    status = Slide.SlideStatus.draft
