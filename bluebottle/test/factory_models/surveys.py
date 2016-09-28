import factory

from bluebottle.surveys.models import Survey, Question, Answer, Response, SubQuestion


class SurveyFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Survey


class QuestionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Question


class SubQuestionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = SubQuestion


class AnswerFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Answer


class ResponseFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Response
