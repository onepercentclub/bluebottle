import factory

from bluebottle.activities.models import ActivityQuestion, ActivityAnswer, TextQuestion, TextAnswer


class TextQuestionFactory(factory.DjangoModelFactory):

    class Meta:
        model = TextQuestion


class TextAnwserFactory(factory.DjangoModelFactory):
    class Meta:
        model = TextAnswer