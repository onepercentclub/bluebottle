import factory

from bluebottle.activities.models import TextQuestion, TextAnswer, RemoteMember


class TextQuestionFactory(factory.DjangoModelFactory):

    class Meta:
        model = TextQuestion


class TextAnswerFactory(factory.DjangoModelFactory):
    class Meta:
        model = TextAnswer


class RemoteMemberFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = RemoteMember

    email = factory.Sequence(lambda o: u'user_{0}@onepercentclub.com'.format(o))
    first_name = factory.Sequence(lambda name: u'user_{0}'.format(name))
    last_name = factory.Sequence(lambda name: u'user_{0}'.format(name))
