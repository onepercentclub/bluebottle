import factory

from bluebottle.activities.models import TextQuestion, TextAnswer


class TextQuestionFactory(factory.DjangoModelFactory):

    class Meta:
        model = TextQuestion


class TextAnswerFactory(factory.DjangoModelFactory):
    class Meta:
        model = TextAnswer
