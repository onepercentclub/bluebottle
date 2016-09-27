import factory

from bluebottle.surveys.models import Survey, Question, Answer, Response


class SurveyFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Survey


class QuestionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Question


class AnswerFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Answer


class ResponseFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Response
