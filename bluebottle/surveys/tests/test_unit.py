from urlparse import urlparse, parse_qs

from bluebottle.surveys.models import Survey
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.test.factory_models.projects import ProjectFactory, ProjectThemeFactory
from bluebottle.test.factory_models.tasks import TaskFactory
from bluebottle.test.factory_models.surveys import SurveyFactory, QuestionFactory, ResponseFactory, AnswerFactory, \
    SubQuestionFactory


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

        self.survey = SurveyFactory(link='https://example.com/survey/1/', active=True)

    def test_survey_url(self):
        url = urlparse(
            Survey.url(self.task)
        )
        query = parse_qs(url.query)

        self.assertEqual(url.netloc, 'example.com')
        self.assertEqual(query['theme'], [self.theme.slug])
        self.assertEqual(query['project_id'], [str(self.project.id)])
        self.assertEqual(query['task_id'], [str(self.task.id)])
        self.assertEqual(query['user_type'], ['task_member'])

    def test_survey_url_no_survey(self):
        self.survey.delete()

        self.assertIsNone(Survey.url(self.task))

    def test_survey_url_project(self):
        url = urlparse(
            Survey.url(self.project)
        )
        query = parse_qs(url.query)

        self.assertEqual(url.netloc, 'example.com')
        self.assertEqual(query['theme'], [self.theme.slug])
        self.assertEqual(query['project_id'], [str(self.project.id)])
        self.assertTrue('task_id' not in query)

    def test_survey_url_user_type(self):
        url = urlparse(
            Survey.url(self.task, user_type='initiator'),
        )
        query = parse_qs(url.query)

        self.assertEqual(url.netloc, 'example.com')
        self.assertEqual(query['theme'], [self.theme.slug])
        self.assertEqual(query['project_id'], [str(self.project.id)])
        self.assertEqual(query['task_id'], [str(self.task.id)])
        self.assertEqual(query['user_type'], ['initiator'])

    def test_survey_url_no_celebration(self):
        self.project.celebrate_results = False
        self.project.save()

        self.assertIsNone(Survey.url(self.project))


class TestSimpleProjectSurveyAggregation(BluebottleTestCase):
    """
    Check some simple project survey aggregations.
    """

    def setUp(self):
        super(TestSimpleProjectSurveyAggregation, self).setUp()

        self.init_projects()

        self.project = ProjectFactory()
        self.project_2 = ProjectFactory()

        self.survey = SurveyFactory(title='test survey', active=True)

        self.response = ResponseFactory.create(
            project=self.project,
            survey=self.survey
        )

    def test_ignore_sum(self):
        """
        Aggregation=sum only is only intended for tasks-by-project aggregations.
        For project aggregations it should still be mean.
        """
        question = QuestionFactory(survey=self.survey, title='test', aggregation='sum', type='number')

        for value in ['30', '10', '20.0']:
            AnswerFactory.create(
                question=question,
                response=self.response,
                value=value,
            )

        self.survey.aggregate()
        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='project',
                                                     project=self.project)
        self.assertEqual(aggregate.value, 20.0)

    def test_average(self):
        question = QuestionFactory(survey=self.survey, title='test', aggregation='average', type='number')

        for value in ['30', '10', '20.0']:
            AnswerFactory.create(
                question=question,
                response=self.response,
                value=value,
            )

        self.survey.aggregate()
        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='project',
                                                     project=self.project)
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
        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='project',
                                                     project=self.project)
        self.assertEqual(aggregate.value, 10.0)

    def test_slider(self):
        question = QuestionFactory(survey=self.survey, title='how', aggregation='average', type='slider')

        for value in [80, 70, 90]:
            AnswerFactory.create(
                question=question,
                response=self.response,
                value=value,
            )

        self.survey.aggregate()

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='project',
                                                     project=self.project)
        self.assertEqual(aggregate.value, 80.0)

    def test_multiple_choice_radio(self):
        question = QuestionFactory(survey=self.survey, title='test', type='radio')

        for value in ['test', 'toast', 'test']:
            AnswerFactory.create(
                question=question,
                response=self.response,
                options=[value]
            )

        self.survey.aggregate()
        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='project',
                                                     project=self.project)
        self.assertEqual(aggregate.options, {'test': 2, 'toast': 1})

    def test_multiple_choice_checkbox(self):
        question = QuestionFactory(survey=self.survey, title='test', type='checkbox')

        for values in [['test'], ['test', 'toast'], ['test'], ['toast', 'wokkel']]:
            AnswerFactory.create(
                question=question,
                response=self.response,
                options=values
            )

        self.survey.aggregate()
        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='project',
                                                     project=self.project)
        self.assertEqual(aggregate.options, {"test": 3, "wokkel": 1, "toast": 2})

    def test_table_radio(self):
        question = QuestionFactory(survey=self.survey, title='test', type='table-radio')
        SubQuestionFactory(question=question, title='toast')
        SubQuestionFactory(question=question, title='test')

        for values in [{'test': 2, 'toast': 8}, {'test': 4, 'toast': 9}, {'test': 3, 'toast': 7}]:
            AnswerFactory.create(
                question=question,
                response=self.response,
                options=values
            )

        self.survey.aggregate()
        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='project',
                                                     project=self.project)
        # Answers should follow the ordering of sub questions
        self.assertEqual(aggregate.options, {'toast': 8.0, 'test': 3.0})


class TestTaskSurveyAggregation(BluebottleTestCase):
    """
    Check some task survey aggregations.
    """

    def setUp(self):
        super(TestTaskSurveyAggregation, self).setUp()

        self.init_projects()

        self.project = ProjectFactory.create()
        self.task1 = TaskFactory.create(project=self.project)
        self.task2 = TaskFactory.create(project=self.project)
        self.task3 = TaskFactory.create(project=self.project)

        self.survey = SurveyFactory(title='test survey')

        self.project_response = ResponseFactory.create(
            project=self.project,
            survey=self.survey
        )

        self.task_response1 = ResponseFactory.create(
            project=self.project,
            task=self.task1,
            survey=self.survey
        )

        self.task_response2 = ResponseFactory.create(
            project=self.project,
            task=self.task2,
            survey=self.survey
        )

        self.task_response3 = ResponseFactory.create(
            project=self.project,
            task=self.task3,
            survey=self.survey
        )

    def test_average(self):
        question = QuestionFactory(survey=self.survey, title='test', aggregation='average', type='number')

        for value in ['10', '20', '30']:
            AnswerFactory.create(
                question=question,
                response=self.task_response1,
                value=value,
            )

        for value in ['50']:
            AnswerFactory.create(
                question=question,
                response=self.task_response2,
                value=value,
            )

        for value in ['80']:
            AnswerFactory.create(
                question=question,
                response=self.task_response3,
                value=value,
            )

        self.survey.aggregate()

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='task',
                                                     task=self.task1,
                                                     project=self.project)
        self.assertEqual(aggregate.value, 20.0)

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='task',
                                                     task=self.task2,
                                                     project=self.project)
        self.assertEqual(aggregate.value, 50.0)

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='task',
                                                     task=self.task3,
                                                     project=self.project)
        self.assertEqual(aggregate.value, 80.0)

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='project_tasks',
                                                     project=self.project)
        self.assertEqual(aggregate.value, 50.0)

    def test_sum(self):
        question = QuestionFactory(survey=self.survey, title='test', aggregation='sum', type='number')

        for value in ['10', '20', '30']:
            AnswerFactory.create(
                question=question,
                response=self.task_response1,
                value=value,
            )

        for value in ['50']:
            AnswerFactory.create(
                question=question,
                response=self.task_response2,
                value=value,
            )

        for value in ['90']:
            AnswerFactory.create(
                question=question,
                response=self.task_response3,
                value=value,
            )

        self.survey.aggregate()

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='project_tasks',
                                                     project=self.project)
        self.assertEqual(aggregate.value, 160.0)

    def test_list(self):
        question = QuestionFactory(survey=self.survey, title='shoot', type='list')

        for value in ['Panda', 'Elephant', 'Rhino']:
            AnswerFactory.create(
                question=question,
                response=self.task_response1,
                value=value,
            )

        for value in ['Hedgehog']:
            AnswerFactory.create(
                question=question,
                response=self.task_response2,
                value=value,
            )

        for value in ['Bear', 'Lion']:
            AnswerFactory.create(
                question=question,
                response=self.task_response3,
                value=value,
            )

        self.survey.aggregate()

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='task',
                                                     task=self.task1,
                                                     project=self.project)
        self.assertListEqual(aggregate.list, ['Elephant', 'Panda', 'Rhino'])

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='project_tasks',
                                                     project=self.project)
        self.assertEqual(aggregate.list, ['Bear', 'Elephant', 'Hedgehog', 'Lion', 'Panda', 'Rhino'])

    def test_multiple_choice_radio(self):
        question = QuestionFactory(survey=self.survey, title='test', type='table-radio')
        SubQuestionFactory(question=question, title='test')
        SubQuestionFactory(question=question, title='toast')

        for values in [{'test': 2, 'toast': 8}, {'test': 4, 'toast': 9}, {'test': 3, 'toast': 7}]:
            AnswerFactory.create(
                question=question,
                response=self.task_response1,
                options=values
            )

        for values in [{'test': 1, 'toast': 9}]:
            AnswerFactory.create(
                question=question,
                response=self.task_response2,
                options=values
            )

        self.survey.aggregate()

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='task',
                                                     task=self.task1)
        self.assertEqual(aggregate.options, {'test': 3.0, 'toast': 8.0})

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='task',
                                                     task=self.task2)
        self.assertEqual(aggregate.options, {'test': 1.0, 'toast': 9.0})

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='project_tasks',
                                                     project=self.project)
        self.assertEqual(aggregate.options, {'test': 2.0, 'toast': 8.5})


class TestCombinedSurveyAggregation(BluebottleTestCase):
    """
    Check some task survey aggregations.
    """

    def setUp(self):
        super(TestCombinedSurveyAggregation, self).setUp()

        self.init_projects()

        self.project = ProjectFactory.create()
        self.task1 = TaskFactory.create(project=self.project)
        self.task2 = TaskFactory.create(project=self.project)
        self.task3 = TaskFactory.create(project=self.project)

        self.survey = SurveyFactory(title='test survey')

        self.intitiator_response = ResponseFactory.create(
            project=self.project,
            user_type='initiator',
            survey=self.survey
        )

        self.organization_response = ResponseFactory.create(
            project=self.project,
            user_type='organization',
            survey=self.survey
        )

        self.task_response1 = ResponseFactory.create(
            project=self.project,
            task=self.task1,
            survey=self.survey
        )

        self.task_response2 = ResponseFactory.create(
            project=self.project,
            task=self.task2,
            survey=self.survey
        )

        self.task_response3 = ResponseFactory.create(
            project=self.project,
            task=self.task3,
            survey=self.survey
        )

    def test_project_aggregates(self):

        question1 = QuestionFactory(survey=self.survey, title='test', aggregation='sum', type='number')

        for value in ['110', '130']:
            AnswerFactory.create(
                question=question1,
                response=self.intitiator_response,
                value=value,
            )

        self.survey.aggregate()

        aggregate = question1.aggregateanswer_set.get(question=question1,
                                                      aggregation_type='project',
                                                      project=self.project)

        self.assertEqual(aggregate.value, 120.0)

    def test_combined_number(self):

        question = QuestionFactory(survey=self.survey, title='test', aggregation='sum', type='number')

        for value in ['110', '130']:
            AnswerFactory.create(
                question=question,
                response=self.intitiator_response,
                value=value,
            )

        for value in ['200']:
            AnswerFactory.create(
                question=question,
                response=self.organization_response,
                value=value,
            )

        for value in ['10', '20', '30']:
            AnswerFactory.create(
                question=question,
                response=self.task_response1,
                value=value,
            )

        for value in ['50']:
            AnswerFactory.create(
                question=question,
                response=self.task_response2,
                value=value,
            )

        for value in ['90']:
            AnswerFactory.create(
                question=question,
                response=self.task_response3,
                value=value,
            )

        self.survey.aggregate()

        aggregate1 = question.aggregateanswer_set.get(question=question,
                                                      aggregation_type='combined',
                                                      project=self.project)
        # Expected value is calculated
        # initiator:        (110 + 130) / 2
        # organization:     200
        # tasks:            (10 + 20 + 30) / 3 + 50 + 90
        # Mean:             (120 + 200 + 160)/ 3 = 160
        self.assertEqual(aggregate1.value, 160.0)

    def test_combined_table_radio(self):

        question = QuestionFactory(survey=self.survey, title='test', type='table-radio')
        SubQuestionFactory(question=question, title='test')
        SubQuestionFactory(question=question, title='toast')

        for values in [{'test': 4, 'toast': 6}]:
            AnswerFactory.create(
                question=question,
                response=self.intitiator_response,
                options=values
            )

        for values in [{'test': 5, 'toast': 9}, {'test': 7, 'toast': 10}]:
            AnswerFactory.create(
                question=question,
                response=self.organization_response,
                options=values
            )

        for values in [{'test': 2, 'toast': 8}, {'test': 4, 'toast': 9}, {'test': 3, 'toast': 7}]:
            AnswerFactory.create(
                question=question,
                response=self.task_response1,
                options=values
            )

        for values in [{'test': 1, 'toast': 9}]:
            AnswerFactory.create(
                question=question,
                response=self.task_response2,
                options=values
            )

        self.survey.aggregate()

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='task',
                                                     task=self.task1)
        self.assertEqual(aggregate.options, {'test': 3.0, 'toast': 8.0})

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='project_tasks',
                                                     project=self.project)
        self.assertEqual(aggregate.options, {'test': 2.0, 'toast': 8.5})

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='project',
                                                     project=self.project)
        self.assertEqual(aggregate.options, {'test': 5.333333333333333, 'toast': 8.333333333333334})

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='organization',
                                                     project=self.project)
        self.assertEqual(aggregate.options, {'test': 6.0, 'toast': 9.5})

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='initiator',
                                                     project=self.project)
        self.assertEqual(aggregate.options, {'test': 4.0, 'toast': 6.0})

        aggregate = question.aggregateanswer_set.get(question=question,
                                                     aggregation_type='combined',
                                                     project=self.project)
        # Calculation of combined
        # Initiator mean:    {'test': 4.0, 'toast': 6.0}
        # Organization mean: {'test': 6.0, 'toast': 9.5}
        # Tasks mean:        {'test': 2.0, 'toast': 8.5}
        # Combined:          {'test': 4.0, 'toast': 8.0}
        self.assertEqual(aggregate.options, {'test': 4.0, 'toast': 8.0})
