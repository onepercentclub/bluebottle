from bluebottle.clients import properties
from surveygizmo import SurveyGizmo

from bluebottle.surveys.models import Survey, Question


class BaseAdapter(object):

    def get_surveys(self):
        raise NotImplementedError()

    def update_surveys(self):
        for data in self.get_surveys():
            survey, created = Survey.objects.get_or_create(remote_id=data['id'])
            self.update_survey(survey)

    def update_survey(self, remote_id):
        raise NotImplementedError()

    def get_survey(self, remote_id):
        raise NotImplementedError()


class SurveyGizmoAdapter(BaseAdapter):

    def __init__(self):
        self.client = SurveyGizmo(
            api_version='v4',
            api_token = properties.SURVEYGIZMO_API_TOKEN,
            api_token_secret = properties.SURVEYGIZMO_API_SECRET
        )

    def update_survey(self, survey):
        data = self.get_survey(survey.remote_id)
        survey.specification = data
        survey.title = data['title']
        survey.link = data['links']['campaign']
        survey.save()

        for page in data['pages']:
            for quest in page['questions']:
                if quest['_type'] == 'SurveyQuestion':
                    Question.objects.get_or_create(
                        remote_id=quest['id'], survey=survey,
                        defaults={
                            'specification': quest,
                            'title': quest['title']['English'],
                            'type': quest['_subtype']
                        }
                    )

    def get_surveys(self):
        return self.client.api.survey.list()['data']

    def get_survey(self, remote_id):
        return self.client.api.survey.get(remote_id)['data']

