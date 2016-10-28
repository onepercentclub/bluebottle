import random


from django.core.urlresolvers import reverse

from bluebottle.bb_projects.models import ProjectPhase

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.surveys import SurveyFactory, QuestionFactory, ResponseFactory, AnswerFactory


class ProjectSurveyAPITestCase(BluebottleTestCase):
    """
    """
    def setUp(self):
        super(ProjectSurveyAPITestCase, self).setUp()

        self.init_projects()

        phase = ProjectPhase.objects.get(slug='campaign')

        self.project = ProjectFactory.create(status=phase)
        self.survey = SurveyFactory(title='test survey')

        questions = (
            ('Question 1', 'string', None, {}),
            ('Question 2', 'number', 'average', {'max_number': 100, 'min_number': 100}),
            ('Question 3', 'slider', 'sum', {'max_number': 100, 'min_number': 100})
        )

        questions = [
            QuestionFactory.create(
                survey=self.survey,
                title=title,
                type=type,
                aggregation=aggregation,
                properties=properties
            ) for title, type, aggregation, properties in questions]

        response = ResponseFactory.create(
            project=self.project,
            survey=self.survey
        )

        for question in questions:
            AnswerFactory.create(
                question=question,
                response=response,
                value=random.randint(0, 100)
            )

        self.survey_url = reverse('project_survey_list')

    def test_get_survey(self):
        self.survey.aggregate()

        response = self.client.get(self.survey_url, {'project': self.project.slug})
        self.assertEqual(response.status_code, 200)

        data = response.data[0]

        self.assertEqual(data['title'], self.survey.title)

        for answer in data['answers']:
            self.assertTrue('type' in answer)
            self.assertTrue('value' in answer)
            self.assertTrue('title' in answer)
            self.assertTrue('properties' in answer)

    def test_get_survey_no_aggregate(self):
        response = self.client.get(self.survey_url, {'project': self.project.slug})
        self.assertEqual(response.status_code, 200)

        data = response.data[0]

        self.assertEqual(data['title'], self.survey.title)

        for answer in data['answers']:
            self.assertIsNone(answer['value'])
