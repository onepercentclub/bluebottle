from bluebottle.clients import properties
from surveygizmo import SurveyGizmo

from bluebottle.surveys.models import Survey, Question


class BaseAdapter(object):

    def get_surveys(self):
        raise NotImplementedError()

    def update_surveys(self):
        for data in self.get_surveys():
            survey = Survey.objects.get_or_create(remote_id=data['id'])
            self.update_survey(survey)

    def update_survey(self, survey):
        data = self.get_survey(survey.remote_id)
        survey.specification = data
        for page in data['pages']:
            for quest in page['questions']:
                Question.objects.get_or_create(remote_id=quest['id'], default={'specification': quest})

    def get_survey(self, remote_id):
        raise NotImplementedError()

    def get_responses(self, survey):


class SurveyGizmoAdapter(BaseAdapter):

    def __init__(self):
        self.client = SurveyGizmo(
            api_version='v4',
            api_token = properties.SURVEYGIZMO_API_TOKEN,
            api_token_secret = properties.SURVEYGIZMO_API_SECRET
        )

    def get_surveys(self):
        return self.client.api.survey.list()['data']

    def get_survey(self, remote_id):
        return self.client.api.survey.list()['data']

