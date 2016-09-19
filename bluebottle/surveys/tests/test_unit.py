from urlparse import urlparse, parse_qs
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.test.factory_models.projects import ProjectFactory, ProjectThemeFactory
from bluebottle.test.factory_models.tasks import TaskFactory
from bluebottle.test.factory_models.surveys import SurveyFactory


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
