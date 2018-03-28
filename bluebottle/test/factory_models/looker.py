from bluebottle.looker.models import LookerEmbed
import factory


class LookerEmbedFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = LookerEmbed
