from urlparse import urlparse, parse_qs

from bluebottle.surveys.models import Answer
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.test.factory_models.projects import ProjectFactory, ProjectThemeFactory
from bluebottle.test.factory_models.tasks import TaskFactory
from bluebottle.test.factory_models.surveys import SurveyFactory, QuestionFactory, ResponseFactory, AnswerFactory


class TestProjectStatusUpdate(BluebottleTestCase):
    """
        save() automatically updates some fields, specifically
        the status field. Make sure it picks the right one
    """

    def setUp(self):
        super(TestProjectStatusUpdate, self).setUp()

        self.init_projects()

        self.theme = ProjectThemeFactory(slug='test-theme')
        self.project = ProjectFactory(theme=self.theme)
        self.task = TaskFactory(project=self.project)

        self.survey = SurveyFactory(link='https://example.com/survey/1/')

    def test_survey_url(self):
        url = urlparse(
            self.survey.url(self.task)
        )
        query = parse_qs(url.query)

        self.assertEqual(url.netloc, 'example.com')
        self.assertEqual(query['theme'], [self.theme.slug])
        self.assertEqual(query['project_id'], [str(self.project.id)])
        self.assertEqual(query['task_id'], [str(self.task.id)])


class TestAggregation(BluebottleTestCase):
    """
        save() automatically updates some fields, specifically
        the status field. Make sure it picks the right one
    """

    def setUp(self):
        super(TestAggregation, self).setUp()

        self.init_projects()

        self.project = ProjectFactory()
        self.project_2 = ProjectFactory()

        self.survey = SurveyFactory(title='test survey')

        self.response = ResponseFactory.create(
            project=self.project,
            survey=self.survey
        )

    def test_sum(self):
        question = QuestionFactory(survey=self.survey, title='test', aggregation='sum', type='number')

        for value in ['30', '10', '20.0']:
            AnswerFactory.create(
                question=question,
                response=self.response,
                value=value,
            )

        self.survey.aggregate()
        aggregate = question.aggregateanswer_set.get(question=question, project=self.project)
        self.assertEqual(aggregate.value, 60.0)

    def test_average(self):
        question = QuestionFactory(survey=self.survey, title='test', aggregation='average', type='number')

        for value in ['30', '10', '20.0']:
            AnswerFactory.create(
                question=question,
                response=self.response,
                value=value,
            )

        self.survey.aggregate()
        aggregate = question.aggregateanswer_set.get(question=question, project=self.project)
        self.assertEqual(aggregate.value, 20.0)

    def test_average_non_number(self):
        question = QuestionFactory(survey=self.survey, title='test', aggregation='average', type='number')

        for value in ['20', '10', 'onzin test']:
            AnswerFactory.create(
                question=question,
                response=self.response,
                value=value,
            )

        self.survey.aggregate()
        aggregate = question.aggregateanswer_set.get(question=question, project=self.project)
        self.assertEqual(aggregate.value, 10.0)

    def test_multiplechoice_radio(self):
        question = QuestionFactory(survey=self.survey, title='test', type='radio')

        for value in ['test', 'tast', 'test']:
            AnswerFactory.create(
                question=question,
                response=self.response,
                options=[value]
            )

        self.survey.aggregate()
        aggregate = question.aggregateanswer_set.get(question=question, project=self.project)
        self.assertEqual(aggregate.options, {'test': 2, 'tast': 1})

    def test_multiplechoice_checkbox(self):
        question = QuestionFactory(survey=self.survey, title='test', type='checkbox')

        for values in [['test'], ['test', 'tast'], ['test'], ['tast', 'wokkel']]:
            AnswerFactory.create(
                question=question,
                response=self.response,
                options=values
            )

        self.survey.aggregate()
        aggregate = question.aggregateanswer_set.get(question=question, project=self.project)
        self.assertEqual(aggregate.options, {"test": 3, "wokkel": 1, "tast": 2})

    def test_table_radio(self):
        question = QuestionFactory(survey=self.survey, title='test', type='table-radio')


        for values in [{'test': 2, 'tast': 8}, {'test': 4, 'tast': 9}, {'test': 3, 'tast': 7}]:
            AnswerFactory.create(
                question=question,
                response=self.response,
                options=values
            )

        self.survey.aggregate()
        aggregate = question.aggregateanswer_set.get(question=question, project=self.project)
        self.assertEqual(aggregate.options, {'test': 3.0, 'tast': 8.0})





